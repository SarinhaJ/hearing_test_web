from flask import Flask, render_template, request, redirect, url_for
import os
import glob
import random

app = Flask(__name__)

# 全局变量来存储测试状态
participant_code = None
audio_files = []  # 存储音频文件信息的列表
current_audio_index = 0
test_results = []

# 初始化音频文件列表
def get_audio_files_list():
    audio_files = []
    audio_folder = 'static/audio/noisy_audio_files'
    file_paths = glob.glob(os.path.join(audio_folder, 'noisy_snr_*.wav'))
    for file_path in sorted(file_paths):
        file_name = os.path.basename(file_path)
        # 从文件名中提取SNR和正确答案
        parts = file_name.replace('.wav', '').split('_')
        # 处理负数SNR的情况
        try:
            snr = int(parts[2])
        except ValueError:
            snr = int(parts[2] + parts[3])  # 如果SNR是负数，例如'-10'
            words_start_index = 4
        else:
            words_start_index = 3
        correct_answers = '_'.join(parts[words_start_index:])
        audio_files.append({
            'file_name': file_name,
            'snr': snr,
            'correct_answers': correct_answers
        })
    # 如果需要随机化顺序
    # random.shuffle(audio_files)
    return audio_files

@app.route('/', methods=['GET', 'POST'])
def index():
    global participant_code, audio_files, current_audio_index
    if request.method == 'POST':
        participant_code = request.form['participant_code']
        audio_files = get_audio_files_list()
        current_audio_index = 0
        return redirect(url_for('test'))
    return render_template('index.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    global current_audio_index, audio_files, test_results

    if current_audio_index >= len(audio_files):
        # 测试完成，保存结果
        save_results()
        return redirect(url_for('thank_you'))

    audio_info = audio_files[current_audio_index]
    audio_filename = audio_info['file_name']
    snr = audio_info['snr']
    correct_answers = audio_info['correct_answers']

    if request.method == 'POST':
        response = request.form['response']
        clarity_count = request.form['clarity_count']
        # 记录结果
        test_results.append({
            'snr': snr,
            'response': response,
            'correct_answers': correct_answers,
            'clarity_count': clarity_count
        })
        current_audio_index += 1
        # 在提交后显示正确答案
        return render_template('feedback.html', correct_answers=correct_answers, next_url=url_for('test'))
    return render_template('test.html', audio_file=url_for('static', filename=f'audio/noisy_audio_files/{audio_filename}'), snr=snr)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

def save_results():
    global participant_code, test_results
    if not os.path.exists('results'):
        os.makedirs('results')
    results_path = f"results/{participant_code}_noise_pretest_results.txt"
    with open(results_path, 'w') as f:
        for result in test_results:
            f.write(f"SNR: {result['snr']}, Response: {result['response']}, Correct Answers: {result['correct_answers']}, Clarity: {result['clarity_count']}\n")
    # 重置测试状态
    reset_test()

def reset_test():
    global participant_code, current_audio_index, test_results, audio_files
    participant_code = None
    current_audio_index = 0
    test_results = []
    audio_files = []

if __name__ == '__main__':
    app.run(debug=True)
