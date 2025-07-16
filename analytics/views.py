from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DatasetForm
from .models import Dataset, AnalysisResult
import requests
from django.http import Http404
from .forms import DatasetForm
import logging
from .models import Dataset

logger = logging.getLogger(__name__)  # Optional: Enable logging


def analytics_home(request):
    # Your logic for the analytics home page
    # Ensure this template exists
    return render(request, 'home.html')  # No 'analytics/' prefix

                                                                                                                                                     
@login_required
def upload_dataset(request):
    if request.method == 'POST':
        form = DatasetForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.user = request.user
            dataset.save()
            return redirect('analyze', dataset_id=dataset.id)
    else:
        form = DatasetForm()
    return render(request, 'analytics/registration/upload.html', {'form': form})


@login_required
def analyze_data(request, dataset_id):
    try:
        dataset = Dataset.objects.get(id=dataset_id, user=request.user)
    except Dataset.DoesNotExist:
        raise Http404("Dataset not found")

    try:
        with dataset.file.open('rb') as f:
            response = requests.post(
                'http://localhost:5000/predict',  # Your Flask ML API
                files={'file': (dataset.file.name, f, 'multipart/form-data')},
                timeout=15  # Prevent hanging forever
            )

        # ✅ Handle response from Flask API
        if response.status_code == 200:
            try:
                result = response.json()
            except ValueError:
                return render(request, 'analytics/error.html', {
                    'error': 'Received invalid JSON from prediction server.'
                })

            return render(request, 'analytics/results.html', {
                'dataset': dataset,
                'predictions': result.get('predictions', []),
                'prescriptions': result.get('prescriptions', []),
                'probabilities': result.get('probabilities', []),
            })

        else:
            # 🧠 Try extracting specific error message
            try:
                error_msg = response.json().get('error', 'Analysis failed')
            except ValueError:
                error_msg = response.text or 'Analysis failed'

            return render(request, 'analytics/error.html', {'error': error_msg})

    except requests.exceptions.RequestException as e:
        logger.error(f"Prediction API call failed: {e}")
        return render(request, 'analytics/error.html', {
            'error': 'Could not connect to the prediction server. Please ensure it is running.'
        })
