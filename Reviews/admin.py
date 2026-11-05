from django.contrib import admin
from .models import ProductQuestion, Review, ReviewImage, ReviewReport

admin.site.register(Review)
admin.site.register(ReviewImage)
admin.site.register(ReviewReport)
admin.site.register(ProductQuestion)
