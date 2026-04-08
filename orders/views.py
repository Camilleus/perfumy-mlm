from django.shortcuts import redirect
from django.http import JsonResponse
from products.models import Product
from .cart import Cart

def cart_add(request, pk):
    cart = Cart(request)
    product = Product.objects.get(pk=pk)
    cart.add(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))

def cart_remove(request, pk):
    cart = Cart(request)
    cart.remove(pk)
    return redirect('cart_detail')

def cart_detail(request):
    from django.shortcuts import render
    cart = Cart(request)
    return render(request, 'orders/cart.html', {'cart': cart})