import os
from django.conf import settings
import re
import csv
import re
from openai import AsyncAzureOpenAI
import asyncio
import pandas as pd
from openpyxl import Workbook
from openai import BadRequestError
import time

async def process_data():

    input_file = os.path.join(settings.MEDIA_ROOT, 'uploaded.csv')
    output_file = os.path.join(settings.MEDIA_ROOT, 'cleaned_output.csv')

    cleaned_data = []
    form_names_set = set()  # Set to store unique form names

    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        index = 0  # Initialize index
        for line in reader:
            if len(line) > 7 and line[6]:  # Check if line has enough elements and JSON data is not empty
                form_id = line[4]
                form_name = line[3]
                vertical = line[1].split(',')[1] if ',' in line[1] else line[1]  # Extracting the second element after splitting by ","
                json_data = line[6].replace('""', '"')  # Replacing double double-quotes with single double-quote
                
                # Extracting column names using regular expression to find all occurrences of ""label"":""<content>""
                column_names = re.findall(r'"label":"(.*?)"', json_data)

                # Decode escaped Unicode characters
                decoded_column_names = [bytes(column_name, 'utf-8').decode('unicode_escape') for column_name in column_names]
                
                nb_submissions = int(line[7]) if line[7] else 0  # Extract number of submissions
                
                # Check if form has submissions and if its name is unique
                if nb_submissions > 0 and form_name not in form_names_set:
                    cleaned_data.append((index, form_id, vertical, form_name, decoded_column_names, nb_submissions, "https://scn-hub-digital.daxium-air.com/"+vertical+"/submissions/"+form_id+"/table"))
                    form_names_set.add(form_name)  # Add form name to set to mark it as seen
                    index += 1  # Increment index
                
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['Index', 'ID', 'Vertical', 'Nom', 'Champs', 'Nb Submissions', 'URL'])
        writer.writerows(cleaned_data)

    client = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview"
    )

    async def process_row(row, client, ws):
        try:
            # Clean the "Champs RGPD" field
            champs = (
                row["Champs"]
                .replace("\\/", "")
                .replace("\/", "")
                .replace("'", "")
                .replace('"', "")
                .replace("-", "")
                .replace(":", "")
            )

            # Obtenir la réponse du modèle
            response = await client.chat.completions.create(
                model="ModeleGPT4Turbo-dev-test-SWED",
               messages=[
                {"role": "system", "content": "Tu es un assistant AI chargé de détecter les champs RGPD. Ta réponse doit être précise et ne contenir que les champs RGPD, séparés par des virgules. Si aucun champ RGPD n'est détecté, tu dois ne rien retourner."},
                {"role": "user", "content": f"Donne-moi les champs RGPD (données personnelles, traitement, consentement, finalité, exactitude, limitation de la conservation, sécurité, transfert, responsabilité, droit d'accès, droit de rectification, droit à l'effacement, droit à la limitation du traitement, droit à la portabilité des données, droit d'opposition, autorité de contrôle) à partir de ces champs : {champs}"}
                ]
            )

            # Récupérer le résultat du modèle
            model_result = response.choices[0].message.content

            if model_result != "":
                ws.append([f"{row['ID']}", row['Vertical'], row['Nom'], model_result, row['URL']])
        except BadRequestError:
            pass 

    BATCH_SIZE = 100  # Number of rows to process per batch
    RATE_LIMIT_PERIOD = 60

    async def main():
        loop = asyncio.get_event_loop()  # Get the event loop
        # Load CSV file and create Excel workbook
        df = pd.read_csv(output_file)
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Vertical", "Nom", "Champs RGPD", "URL"])

        # Determine the number of rows to process
        total_rows = len(df)

        # Determine the number of batches needed
        num_batches = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE

        # Process batches within the rate limit
        for batch_num in range(num_batches):
            # Calculate the range of rows for the current batch
            start_index = batch_num * BATCH_SIZE
            end_index = min((batch_num + 1) * BATCH_SIZE, total_rows)
            batch_df = df.iloc[start_index:end_index]

            # Process each row in the batch asynchronously
            tasks = [asyncio.create_task(process_row(row, client, ws)) for index, row in batch_df.iterrows()]
            await asyncio.gather(*tasks)

            # Wait for the remaining time in the current minute
            if batch_num < num_batches - 1:
                time_to_wait = RATE_LIMIT_PERIOD - time.time() % RATE_LIMIT_PERIOD
                await asyncio.sleep(time_to_wait)

        # Save the Excel workbook
        excel_file_path = os.path.join(settings.MEDIA_ROOT, "output.xlsx")

        wb.save(excel_file_path)

    # Lancer le programme asynchrone
    await main()