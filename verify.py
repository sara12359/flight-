import os
import django
import unittest
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flight_project.settings')
django.setup()

from flights.tests import FlightSearchTests

import sys
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(FlightSearchTests)
    unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
