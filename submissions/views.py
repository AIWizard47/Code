from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from problems.models import ContestRegistration, Problem
from django.db.models import Count, Q
from .models import Submission
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import tempfile
import subprocess
from django_ratelimit.decorators import ratelimit
import os
from problems.models import Contest, ContestSubmission
from django.utils import timezone

@csrf_exempt
@ratelimit(key='ip', rate='1/s', block=True)
def submit_code(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)

    if request.method == 'POST':
        problem_id = request.POST.get('problem_id')
        code = request.POST.get('code')
        language = request.POST.get('language')

        problem = get_object_or_404(Problem, id=problem_id)

        verdict = 'Accepted'
        error = ''
        test_results = []

        try:
            for idx, test_case in enumerate(problem.test_cases.all()):
                stdout, stderr = run_code(code, language, test_case.input_data)

                def normalize_output(output):
                    lines = output.strip().replace('\r\n', '\n').split('\n')
                    return '\n'.join(line.rstrip() for line in lines)

                actual_output = normalize_output(stdout)
                expected_output = normalize_output(test_case.expected_output)

                if stderr:
                    verdict = 'Runtime Error'
                    error = stderr
                    test_results.append({
                        'test_case': idx + 1,
                        'status': 'Runtime Error',
                        'error': stderr
                    })
                    break

                if actual_output != expected_output:
                    verdict = 'Wrong Answer'
                    test_results.append({
                        'test_case': idx + 1,
                        'status': 'Failed',
                        'expected': expected_output,
                        'actual': actual_output
                    })
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

        except Exception as e:
            verdict = 'Runtime Error'
            error = str(e)

        # Save submission record
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


def run_code(code, language, input_data):
    result = None
    error = ''
    temp_dir = tempfile.mkdtemp()

    try:
        if language == 'python':
            file_path = os.path.join(temp_dir, 'main.py')
            with open(file_path, 'w') as f:
                f.write(code)
            result = subprocess.run(
                ['python', file_path],
                input=input_data.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

        elif language == 'cpp':
            source_path = os.path.join(temp_dir, 'main.cpp')
            binary_path = os.path.join(temp_dir, 'main')
            with open(source_path, 'w') as f:
                f.write(code)

            compile = subprocess.run(
                ['g++', source_path, '-o', binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if compile.returncode != 0:
                error = compile.stderr.decode()
                return '', error

            result = subprocess.run(
                [binary_path],
                input=input_data.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

        elif language == 'java':
            source_path = os.path.join(temp_dir, 'Main.java')
            with open(source_path, 'w') as f:
                f.write(code)

            compile = subprocess.run(
                ['javac', source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if compile.returncode != 0:
                error = compile.stderr.decode()
                return '', error

            result = subprocess.run(
                ['java', '-cp', temp_dir, 'Main'],
                input=input_data.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

        else:
            error = 'Unsupported language.'
            return '', error

        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        return stdout, stderr

    finally:
        # Cleanup
        try:
            for file in os.listdir(temp_dir):
                os.unlink(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
        except:
            pass


@csrf_exempt
@login_required
def submit_contest_code(request):
    if request.method == 'POST':
        contest_id = request.POST.get('contest_id')
        problem_id = request.POST.get('problem_id')
        code = request.POST.get('code')
        language = request.POST.get('language')

        contest = get_object_or_404(Contest, id=contest_id)
        problem = get_object_or_404(Problem, id=problem_id)

        now = timezone.now()
        if not (contest.start_time <= now <= contest.end_time):
            return JsonResponse({'error': 'Contest is not active.'}, status=400)

        # Before running code
        if not ContestRegistration.objects.filter(user=request.user, contest=contest).exists():
            return JsonResponse({'error': 'You must register for the contest first.'}, status=403)

        # (Run code here exactly like before, returning verdict/output...)
        verdict = 'Accepted'
        output_summary = ''
        error = ''
        test_results = []
        try:
            for idx, test_case in enumerate(problem.test_cases.all()):
                stdout, stderr = run_code(code, language, test_case.input_data)

                def normalize_output(output):
                    lines = output.strip().replace('\r\n', '\n').split('\n')
                    return '\n'.join(line.rstrip() for line in lines)

                actual_output = normalize_output(stdout)
                expected_output = normalize_output(test_case.expected_output)

                if stderr:
                    verdict = 'Runtime Error'
                    error = stderr
                    test_results.append({
                        'test_case': idx + 1,
                        'status': 'Runtime Error',
                        'error': stderr
                    })
                    break

                if actual_output != expected_output:
                    verdict = 'Wrong Answer'
                    test_results.append({
                        'test_case': idx + 1,
                        'status': 'Failed',
                        'expected': expected_output,
                        'actual': actual_output
                    })
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

        except Exception as e:
            verdict = 'Runtime Error'
            error = str(e)

        # Save ContestSubmission
        ContestSubmission.objects.update_or_create(
            user=request.user,
            contest=contest,
            problem=problem,
            defaults={
                'code': code,
                'language': language,
                'verdict': verdict,
                'output': str(test_results),
                'error': error
            }
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

def leaderboard(request):
    # Aggregate unique problems solved per user
    users = (
        User.objects.annotate(
            solved_count=Count(
                'submission__problem',
                filter=Q(submission__verdict='Accepted'),
                distinct=True
            )
        )
        .order_by('-solved_count','date_joined')
    )
    return render(request, 'submissions/leaderboard.html', {'users': users})