from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from problems.models import Problem
from .models import Submission
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import tempfile
import subprocess
import os


@csrf_exempt
def submit_code(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)

    if request.method == 'POST':
        problem_id = request.POST.get('problem_id')
        code = request.POST.get('code')
        language = request.POST.get('language')
        # user_id = request.POST.get('user_id')  # TODO: replace with request.user

        # user = User.objects.get(id=user_id)
        problem = get_object_or_404(Problem, id=problem_id)

        verdict = 'Accepted'
        output_summary = ''
        error = ''
        test_results = []

        fd, path = tempfile.mkstemp(suffix=".py")
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(code)
                
            for idx, test_case in enumerate(problem.test_cases.all()):
                try:
                    result = subprocess.run(
                        ['python', path],
                        input=test_case.input_data.encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5
                    )
                    actual_output = result.stdout.decode().strip()
                    expected_output = test_case.expected_output.strip()

                    if actual_output != expected_output:
                        verdict = 'Wrong Answer'
                        test_results.append({
                            'test_case': idx + 1,
                            'status': 'Failed',
                            'expected': expected_output,
                            'actual': actual_output
                        })
                        # Stop on first fail
                        break
                    else:
                        test_results.append({
                            'test_case': idx + 1,
                            'status': 'Passed'
                        })

                except subprocess.TimeoutExpired:
                    verdict = 'Time Limit Exceeded'
                    test_results.append({
                        'test_case': idx + 1,
                        'status': 'Time Limit Exceeded'
                    })
                    break

        except Exception as e:
            verdict = 'Runtime Error'
            error = str(e)
        finally:
            os.unlink(path)

        # Save submission
        Submission.objects.create(
            user=user,
            problem=problem,
            code=code,
            language=language,
            verdict=verdict,
            output=str(test_results),
            error=error
        )

        return JsonResponse({
            'verdict': verdict,
            'test_results': test_results,
            'error': error
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)



@login_required
def submission_history(request):
    submissions = Submission.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'submissions/history.html', {'submissions': submissions})