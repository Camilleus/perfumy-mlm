from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Product

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('id', 'name', 'brand', 'slug', 'price', 'gender', 'category', 'concentration', 'scent_notes', 'intensity', 'occasion', 'description', 'stock_quantity', 'is_available', 'image')

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]
    list_display = ['name', 'brand', 'price', 'stock_quantity', 'gender', 'category', 'concentration', 'is_available']
    list_filter = ['brand', 'gender', 'category', 'concentration', 'intensity', 'occasion', 'is_available']
    search_fields = ['name', 'brand', 'scent_notes']
    list_editable = ['price', 'stock_quantity', 'is_available']
    prepopulated_fields = {'slug': ('brand', 'name')}
    ordering = ('name',)   # <--- dodaj tę linię