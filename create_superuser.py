#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_edu.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Delete if exists
User.objects.filter(username='vtorg').delete()

# Create superuser
User.objects.create_superuser('vtorg', 'vtorg@example.com', '123456')
print("Superuser 'vtorg' created successfully with password '123456'")

