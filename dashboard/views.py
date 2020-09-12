from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import auth
from django.contrib.auth import get_user_model
from django.conf import settings
import requests
import json
from .models import User
import uuid
from django.contrib.auth.views import logout_then_login
import urllib.parse
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.mail import send_mail
# Home page view
from django.contrib.auth import authenticate, login, logout

from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from easy_pdf import rendering
from django.http import JsonResponse


# Create your views here.
from .models import Supplier, Inventory, Transaction, SupplierProductCostView


def signin(request):   
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = authenticate(username = username, password = password)
            if user is not None:
                login(request, user)
                return redirect(reverse('home'))
            else:
                messages.info(request, 'Invalid credentials')
                return render(request, 'login.html') 
        except Exception as err:
            print(err)
            messages.error(request, 'Something went sideways!')
            return render(request, 'login.html') 
    return render(request,'login.html')

def logout_user(request):
    logout(request)
    return redirect(reverse('signin'))


@login_required(login_url='signin')
def dashboard(request):
    return render(request, 'index.html')



@login_required(login_url='signin')
def index(request):
    suppliers       = Supplier.objects.all()
    context         = {
        'suppliers':suppliers,
    }
    return render(request, 'home/index.html', context)

@login_required(login_url='signin')
def inventory(request):
    inventory       = Inventory.objects.all().order_by('id')
    total_products  = Inventory.objects.all().count()
    total_value     = [ i.quantity * i.selling_price for i in inventory]
    context         = {
        'inventory':inventory,
        'total_products':total_products,
        'total_value': sum(total_value)
    }
    return render(request, 'home/index.html', context)

@login_required(login_url='signin')
def checkout(request, *args, **kwargs):
    user            = request.user
    inventory       = Inventory.objects.all().order_by('id')
    cart            = Transaction.objects.all().filter(uid_id = user.id,success=0)
    context         = {
        'checkout':1,
        'inventory_checkout':inventory,
        'cart':cart,
    }

    if request.method == 'POST' and request.POST.get('tiddel'):
        tid = int(request.POST.get('tiddel'))
        Transaction.objects.get(pk=tid).delete()
        cart            = Transaction.objects.all().filter(uid_id = user.id,success=0)
        context['cart'] = cart
        return render(request,'home/index.html', context)

    if request.method == 'POST' and request.POST.get('checkoutrequest'):
        tobj            = Transaction.objects.all().filter(uid_id=user.id,success=False)
        for i in tobj:
            iobj = Inventory.objects.get(pk=i.pid_id)
            print(type(iobj.quantity),iobj.quantity)
            if iobj.quantity > 0 and (iobj.quantity - i.quantity_r) > 0:
                i.success = True
                i.save()
                iobj.quantity = iobj.quantity - i.quantity_r
                iobj.save()

        cart            = Transaction.objects.all().filter(uid_id = user.id,success=False)
        context['cart'] = cart
        return render(request,'home/index.html', context)

    if request.method == 'POST':
        pid             = request.POST['pid']
        print("PID : ",pid)
        iobj            = Inventory.objects.get(pk=pid)
        cname           = request.POST['cname']
        qreq            = request.POST['qreq']
        if int(qreq) <= iobj.quantity:
            tobj        = Transaction.objects.create(cust_name=cname,pid_id=iobj.id,uid_id=user.id,quantity_r=qreq)
            tobj.save()
    
    return render(request,'home/index.html', context)


@login_required(login_url='signin')
def transaction(request):
    user = request.user
    tobj = Transaction.objects.all().filter(uid_id = user.id, success=True)
    context = {
        'transactions':tobj,
    }

    if request.method == 'POST' and request.POST.get('tiddel'):
        tid = int(request.POST.get('tiddel'))
        Transaction.objects.get(pk=tid).delete()
        tobj                    = Transaction.objects.all().filter(uid_id = user.id, success=True)
        context['transactions'] = tobj
        return render(request,'home/index.html', context)

    return render(request,'home/index.html', context)

@login_required(login_url='signin')
def report(request):
    user = request.user
    inventory = Inventory.objects.all()
    tobj = Transaction.objects.all().filter(uid_id = user.id, success=True)
    context = {
        'report':1,
        'inventory_report':inventory,
        'transaction_report':tobj,
        'user':request.user
    }
    if request.method == 'POST' and request.POST.get('ireport'):
        return rendering.render_to_pdf_response(request, 'home/ipdf.html', context, using=None, download_filename=None, content_type='application/pdf', response_class=HttpResponse)

    if request.method == 'POST' and request.POST.get('treport'):
        return rendering.render_to_pdf_response(request, 'home/tpdf.html', context, using=None, download_filename=None, content_type='application/pdf', response_class=HttpResponse)
    return render(request,'home/index.html', context)


def chart(request):
    listOfSuppliers = [i['sname'] for i in SupplierProductCostView.objects.all().values('sname')]
    dataOfProducts  = [i['price'] if i['price'] is not None else 0 for i in SupplierProductCostView.objects.all().values('price')]
    print(listOfSuppliers,dataOfProducts)
    context = {
        'listOfSuppliers':listOfSuppliers,
        'dataOfProducts':dataOfProducts,
    }
    return render(request, 'home/chart.html',context)

