import re
from typing import Dict, List
import edge_tts
import asyncio
import os
import soundfile as sf
import numpy as np

class NovelToSpeech:
    def __init__(self):
        # 定义角色和对应的声音
        self.character_voices = {
            "旁白": "zh-CN-XiaoxiaoNeural",
            "主角": "zh-CN-YunxiNeural",
            "主角独白": "zh-CN-YunjianNeural",
            "配角1": "zh-CN-YunyangNeural",
            "配角2": "zh-CN-XiaochenNeural"
        }
        # 定义需要特殊处理的发音
        self.pronunciation_fixes = {
            "重活": "chóng huó",
            # 可以添加更多需要特殊处理的词
        }
        self.temp_files = []
    
    def parse_text(self, text: str) -> List[Dict]:
        """解析文本，区分对话、内心独白和旁白"""
        segments = []
        
        # 使用正则表达式匹配对话和内心独白
        # 匹配：1. "xxx" 形式的对话
        #      2. 'xxx' 形式的对话
        #      3. 以"我在哪"、"我穿越了"等独立成段的短句作为内心独白
        pattern = r'(?:"([^"]*)"(?:（([^）]*)）)?)|(?:^[^，。？！\n]*(?:我[^，。？！\n]*)[。？！])'
        last_end = 0
        
        for match in re.finditer(pattern, text, re.MULTILINE):
            # 添加对话前的旁白
            if match.start() > last_end:
                narration = text[last_end:match.start()].strip()
                if narration:
                    segments.append({
                        "type": "narration",
                        "text": narration,
                        "voice": self.character_voices["旁白"]
                    })
            
            # 获取匹配的文本
            matched_text = match.group(0)
            
            # 处理引号内的对话
            if match.group(1) is not None:
                dialogue = match.group(1)
                character = match.group(2) if match.group(2) else "主角"
                segments.append({
                    "type": "dialogue",
                    "text": dialogue,
                    "character": character,
                    "voice": self.character_voices.get(character, self.character_voices["主角"])
                })
            # 处理内心独白
            else:
                segments.append({
                    "type": "monologue",
                    "text": matched_text.strip(),
                    "character": "主角",
                    "voice": self.character_voices["主角"]
                })
            
            last_end = match.end()
        
        # 添加最后的旁白（如果有的话）
        if last_end < len(text):
            narration = text[last_end:].strip()
            if narration:
                segments.append({
                    "type": "narration",
                    "text": narration,
                    "voice": self.character_voices["旁白"]
                })
        
        return segments

    def apply_pronunciation_fixes(self, text: str) -> str:
        """应用发音修正"""
        # 按照词语长度从长到短排序，确保先替换较长的词组
        sorted_words = sorted(self.pronunciation_fixes.keys(), key=len, reverse=True)
        
        # 直接替换文本中的词语为拼音
        for word in sorted_words:
            if word in text:
                text = text.replace(word, self.pronunciation_fixes[word])
        return text

    async def generate_audio(self, segments: List[Dict], output_file: str):
        """生成语音文件"""
        try:
            # 生成各个片段的音频
            for i, segment in enumerate(segments):
                temp_file = f"temp_{i}.wav"
                self.temp_files.append(temp_file)
                
                # 如果文本包含需要修正的发音，进行替换
                text = segment["text"]
                if any(word in text for word in self.pronunciation_fixes.keys()):
                    text = self.apply_pronunciation_fixes(text)
                
                # 创建Communicate实例
                communicate = edge_tts.Communicate(text, segment["voice"])
                await communicate.save(temp_file)
            
            # 合并音频文件
            audio_data = []
            sample_rate = None
            
            # 读取所有音频文件
            for temp_file in self.temp_files:
                data, rate = sf.read(temp_file)
                if sample_rate is None:
                    sample_rate = rate
                audio_data.append(data)
            
            # 合并音频数据
            combined = np.concatenate(audio_data)
            
            # 保存合并后的音频
            sf.write(output_file, combined, sample_rate)
            
        finally:
            # 清理临时文件
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            self.temp_files.clear()

async def main():
    converter = NovelToSpeech()
    text = '''
    父亲是老卒，死于十九年前的'山海战役'，随后，母亲也因病去世......想到这里，许七安稍稍有些欣慰。
    众所周知，父母双亡的人都不简单。
    "没想到重活了，还是逃不掉当治安员的宿命？"许七安有些牙疼。
    他父亲前世是一名治安员，因此也希望他能成为一名光荣的治安员。
    可是，许七安虽然走了父母替他选择的道路，他的心却不在体制上。
    他喜欢无拘无束，喜欢自由，喜欢纸醉金迷，喜欢季羡林在日记本里的一句话：
    于是悍然辞职，下海经商。
    "可我为什么会在监狱里？"
    他努力消化着记忆，很快就明白自己眼下的处境。
    '''
    
    segments = converter.parse_text(text)
    await converter.generate_audio(segments, "output.mp3")

if __name__ == "__main__":
    asyncio.run(main()) 