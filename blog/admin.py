from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from .forms import UserAdminCreationForm, UserAdminChangeForm

User = get_user_model()

# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ['email', 'avatar', 'slug', 'sex', 'is_active', 'staff', 'admin', 'create_date', 'update_date', ]
    list_filter = ['admin']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('sex', 'birthday', 'avatar', 'country',)}),
        ('Permissions', {'fields': ('admin', 'staff', 'signup_confirmed',)}),
    )
    list_editable = ['sex', 'staff', 'admin', 'is_active']
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password_2', 'sex', 'birthday')}
         ),
    )
    search_fields = ['email']
    ordering = ['email']
    filter_horizontal = ()


@admin.register(CountryModel)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', ]


@admin.register(SexModel)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', ]


@admin.register(PostModel)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'title', 'slug', 'datetime_create', 'datetime_update']
    exclude = ['slug', ]


@admin.register(TagModel)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    exclude = ['slug', ]


@admin.register(ImagePostModel)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['post', 'image']


@admin.register(EmojisModel)
class EmojisAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji']
    exclude = ['slug', ]


admin.site.register(User, UserAdmin)
