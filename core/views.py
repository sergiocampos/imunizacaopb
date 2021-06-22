from django.utils.translation import gettext as _
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, login, authenticate, logout
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, timezone
from .models import *
import calendar
from time import gmtime, strftime
from django.core.paginator import Paginator
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse, HttpResponseRedirect
from io import BytesIO as IO
from openpyxl import Workbook
from core.forms import UserForm, UserProfileInfoForm
from django.db.models import Max
import base64
from datetime import timedelta
import requests
import pandas as pd
from elasticsearch import Elasticsearch
import elasticsearch.helpers


# Create your views here.
def index(request):
	return render(request,'index.html')


@login_required
def special(request):
	return HttpResponse("You are logged in !")

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect(reverse('index'))

def register(request):
	registered = False
	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileInfoForm(data=request.POST)
		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()
			profile = profile_form.save(commit=False)
			profile.user = user
			#if 'profile_pic' in request.FILES:
			#	print('found it')
			#	profile.profile_pic = request.FILES['profile_pic']
			profile.save()
			registered = True
		else:
			print(user_form.errors,profile_form.errors)
	else:
		user_form = UserForm()
		profile_form = UserProfileInfoForm()
	return render(request,'registration.html', {'user_form':user_form,
		'profile_form':profile_form, 'registered':registered})


def user_login(request):
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(username=username, password=password)
		if user:
			if user.is_active:
				login(request,user)
				return HttpResponseRedirect(reverse('index'))
			else:
				return HttpResponse("Your account was inactive.")
		else:
			print("Someone tried to login and failed.")
			print("They used username: {} and password: {}".format(username,password))
			return HttpResponse("Invalid login details given")
	else:
		return render(request, 'login.html', {})


#codigo a seguir é outro!
@login_required
def signup(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=raw_password)
			login(request, user)
			return redirect('/')
	else:
		form = UserCreationForm()
	return render(request, 'signup.html', {'form': form})


@login_required
def change_password(request):
	if request.method == 'POST':
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)
			messages.success(request, _('Your password was successfully updated!'))
			return redirect('/')
		else:
			messages.error(request, _('Please correct the error below.'))
	else:
		form = PasswordChangeForm(request.user)
	return render(request, 'change_password.html', {'form': form})


@login_required
def search_between_date(request):

	return render(request, 'search_between_date.html')


@login_required
def search_between_date_set(request):
	data_inicio_template = request.POST.get('data_inicio')
	data_fim_template = request.POST.get('data_fim')

	#print("Data inicio capturada:", data_inicio_template)
	#print("Data fim capturada:", data_fim_template)

	#data_inicio = '2021-05-28 12:00:00'
	#data_fim = '2021-05-29 12:00:00'

	data_inicio = datetime.strptime(data_inicio_template, '%Y/%m/%d %H:%M').strftime("%Y-%m-%d %H:%M:%S")
	data_fim = datetime.strptime(data_fim_template, '%Y/%m/%d %H:%M').strftime("%Y-%m-%d %H:%M:%S")

	es  =  Elasticsearch ( 
		[ 'https://imunizacao-es.saude.gov.br/'], 
		http_auth = ( 'imunizacao-covid-pb' ,  'tiliqakera' ), 
		esquema = "https"
	)

	index = 'imunizacao-covid-pb'

	body={"query":{"bool":{"filter":[{"range":{"data_importacao_rnds":{"gte":data_inicio,"lte":data_fim}}}]}}}
	results = elasticsearch.helpers.scan(es, query=body, index=index)
	df = pd.DataFrame.from_dict([document['_source'] for document in results])

	print("numero de casos:",df.shape[0],"de",es.count(index=index)['count'])
	print("coluns:", df.columns)
	#nome = 'imunizacao-{}.csv'.format(datetime.now())
	#nome = nome.replace(':','-')


	response = HttpResponse(content_type='text/csv')

	response['Content-Disposition'] = 'attachment; filename=dados'

	df.to_csv(response, index = False)

	return response