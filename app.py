from quart import Quart, render_template, request, jsonify, send_file
import asyncio
from novel_to_speech import NovelToSpeech
import os
from datetime import datetime
import edge_tts
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

app = Quart(__name__)

# 确保输出目录存在
if not os.path.exists('static/audio'):
    os.makedirs('static/audio')

async def process_segment(segment, start_time, timestamp, segment_index):
    """处理单个文本段落的函数"""
    try:
        # 创建临时文件名
        temp_file = f'static/audio/temp_{timestamp}_{segment_index}.mp3'
        
        # 创建 Communicate 实例并生成音频文件
        communicate = edge_tts.Communicate(segment['text'], segment['voice'])
        await communicate.save(temp_file)
        
        # 获取音频文件的实际长度
        import soundfile as sf
        audio_data, sample_rate = sf.read(temp_file)
        actual_duration = len(audio_data) / sample_rate  # 实际音频长度（秒）
        
        # 分析文本
        chars = list(segment['text'].replace(' ', ''))  # 移除空格
        if not chars:
            return None
            
        # 使用实际音频长度计算每个字符的时长
        time_per_char = actual_duration / len(chars)
        word_timings = []
        current_time = start_time
        
        # 为每个字符分配时间
        for char in chars:
            word_timings.append({
                'text': char,
                'start': current_time,
                'end': current_time + time_per_char
            })
            current_time += time_per_char
        
        return {
            'type': segment['type'],
            'text': segment['text'],
            'start_time': start_time,
            'end_time': start_time + actual_duration,
            'word_timings': word_timings,
            'temp_file': temp_file,
            'index': segment_index
        }
    except Exception as e:
        print(f"Error processing segment {segment_index}: {str(e)}")
        return None

async def process_text(text: str):
    """处理文本并生成音频的异步函数"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'static/audio/output_{timestamp}.mp3'
    
    converter = NovelToSpeech()
    segments = converter.parse_text(text)
    
    # 串行处理每个段落以保持准确的时间戳
    processed_segments = []
    current_time = 0
    
    for i, segment in enumerate(segments):
        result = await process_segment(segment, current_time, timestamp, i)
        if result:
            processed_segments.append(result)
            # 更新下一段的开始时间
            current_time = result['end_time'] + 0.3  # 添加0.3秒的间隔
    
    # 合并音频文件
    import soundfile as sf
    import numpy as np
    
    combined_audio = None
    sample_rate = None
    
    # 按顺序合并音频
    for segment in processed_segments:
        temp_file = segment['temp_file']
        try:
            data, rate = sf.read(temp_file)
            if combined_audio is None:
                combined_audio = data
                sample_rate = rate
            else:
                # 添加短暂的停顿
                silence = np.zeros(int(rate * 0.3))
                combined_audio = np.concatenate([combined_audio, silence, data])
        except Exception as e:
            print(f"Error combining audio: {str(e)}")
        finally:
            # 确保临时文件被删除
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temp file: {str(e)}")
    
    # 保存最终的音频文件
    if combined_audio is not None and sample_rate is not None:
        sf.write(output_file, combined_audio, sample_rate)
    
    # 移除临时文件字段
    for segment in processed_segments:
        segment.pop('temp_file', None)
        segment.pop('index', None)
    
    return {
        'status': 'success',
        'audio_url': output_file,
        'segments': processed_segments
    }

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        data = await request.get_json()
        text = data.get('text')
        if text:
            try:
                result = await process_text(text)
                return jsonify(result)
            except Exception as e:
                print(f"Error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    return await render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 