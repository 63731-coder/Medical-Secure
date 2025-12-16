from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Doctor, Patient, MedicalFile, AppointmentRequest, FileActionRequest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token


class FileApprovalWorkflowTests(TestCase):
	def setUp(self):
		# Create patient user
		self.patient_user = User.objects.create_user(username='patient1', password='pass12345', first_name='Pat', last_name='One')
		self.patient_profile = Patient.objects.create(user=self.patient_user, date_of_birth='1990-01-01')

		# Create doctor user and profile
		self.doctor_user = User.objects.create_user(username='doctor1', password='docpass123', first_name='Doc', last_name='One')
		self.doctor_profile = Doctor.objects.create(user=self.doctor_user, organisation='Test Hospital')

		# Appoint doctor to patient
		# Note: for tests, we'll start without appointment for request flow

		# Clients
		self.client_patient = Client()
		self.client_doctor = Client()

		# Login and get token-like auth via session
		self.client_patient.login(username='patient1', password='pass12345')
		self.client_doctor.login(username='doctor1', password='docpass123')

	def test_patient_upload_and_download(self):
		# Patient uploads a file
		upload = SimpleUploadedFile('report.txt', b'patient data')
		resp = self.client_patient.post('/api/files/', {'file': upload, 'name': 'report.txt', 'description': 'self'}, format='multipart')
		self.assertIn(resp.status_code, (200,201))

		data = resp.json()
		file_id = data.get('id') or data.get('pk')
		self.assertIsNotNone(file_id)

		# Patient can download
		dl = self.client_patient.get(f'/api/files/{file_id}/download/')
		self.assertEqual(dl.status_code, 200)

	def test_doctor_upload_creates_pending_and_patient_approves(self):
		# Doctor attempts to upload for patient (must provide patient_id)
		upload = SimpleUploadedFile('doctor_note.txt', b'doctor data')
		resp = self.client_doctor.post('/api/files/', {'file': upload, 'name': 'doctor_note.txt', 'patient_id': self.patient_profile.id}, format='multipart')
		# Expect creation response
		self.assertIn(resp.status_code, (200,201))
		data = resp.json()
		# Response returns the pending request
		req = data.get('request')
		self.assertIsNotNone(req)
		req_id = req.get('id')
		self.assertIsNotNone(req_id)

		# The FileActionRequest should exist and have no linked medical_file yet
		far = FileActionRequest.objects.get(id=req_id)
		self.assertIsNone(far.medical_file)
		self.assertEqual(far.status, FileActionRequest.STATUS_PENDING)

		# Patient approves
		resp2 = self.client_patient.post('/api/files/respond-file-action/', {'request_id': far.id, 'action': 'approve'})
		self.assertEqual(resp2.status_code, 200)

		# After approval a MedicalFile should be created
		far.refresh_from_db()
		self.assertIsNotNone(far.medical_file)
		mf = far.medical_file
		self.assertTrue(mf.approved)

		# Doctor can now download (after approval)
		dl = self.client_doctor.get(f'/api/files/{mf.id}/download/')
		self.assertEqual(dl.status_code, 200)

	def test_doctor_delete_request(self):
		# Patient uploads a file to be deleted
		upload = SimpleUploadedFile('todelete.txt', b'data')
		resp = self.client_patient.post('/api/files/', {'file': upload, 'name': 'todelete.txt'}, format='multipart')
		self.assertIn(resp.status_code, (200,201))
		mf_id = resp.json().get('id')
		mf = MedicalFile.objects.get(id=mf_id)

		# Appoint the doctor
		self.patient_profile.appointed_doctors.add(self.doctor_profile)

		# Doctor requests deletion
		resp2 = self.client_doctor.delete(f'/api/files/{mf.id}/')
		data = resp2.json()
		self.assertIn('request', data or {})

		far = FileActionRequest.objects.filter(medical_file=mf, action_type=FileActionRequest.ACTION_DELETE).first()
		self.assertIsNotNone(far)
		self.assertEqual(far.status, FileActionRequest.STATUS_PENDING)

		# Patient rejects deletion
		resp3 = self.client_patient.post('/api/files/respond-file-action/', {'request_id': far.id, 'action': 'reject'})
		self.assertEqual(resp3.status_code, 200)

		far.refresh_from_db()
		self.assertEqual(far.status, FileActionRequest.STATUS_REJECTED)

