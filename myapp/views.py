from django.http import JsonResponse
from .scripts.data_process import process_data
from django.shortcuts import render
import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import asyncio


@login_required
def upload_file(request):
    print("upload_file() function called")
    if request.method == 'POST':
        uploaded_file = request.FILES['fileup']
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded.csv')
        with open(file_path, 'wb+') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        return redirect('process')
    else:
        return render(request, 'upload.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('your_name')
        password = request.POST.get('your_pass')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('fileup')
    context = {}
    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def process(request):
    return render(request, 'process.html')


@login_required
def process_data_ajax(request):
    print("process code called")

    # Call the process_data function
    asyncio.run(process_data())

    # Return the result as a JSON response
    response = {      
    }

    return JsonResponse(response)

from django.http import FileResponse
import os

def download_output_file(request):
    # Path to the output file
    file_path = os.path.join(settings.MEDIA_ROOT, 'output.xlsx')
    # Open the file and serve it as a response
    return FileResponse(open(file_path, 'rb'), as_attachment=True)