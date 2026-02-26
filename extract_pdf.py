import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

pdf_path = r"c:\Users\gocom\Documents\Antigravity\Django_BaseCamp\knou_agriculture\data\comcbt\식보기사기출-2023~2024.pdf"
output_path = r"c:\Users\gocom\Documents\Antigravity\Django_BaseCamp\knou_agriculture\data\comcbt\식보기사기출-2023~2024_extracted.txt"

print(f"Uploading file: {pdf_path}")
try:
    sample_file = genai.upload_file(path=pdf_path)
    print(f"Uploaded file '{sample_file.display_name}' as: {sample_file.uri}")
    
    # Wait for the file to be processed
    print("Waiting for file processing...")
    while sample_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        sample_file = genai.get_file(sample_file.name)
    
    if sample_file.state.name == "FAILED":
        print(f"\nFile processing failed.")
        exit(1)
        
    print("\nFile processing completed. Generating content...")
    
    # Use gemini-1.5-pro or gemini-2.5-pro if available
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    prompt = """
이 PDF 파일은 시험 기출문제입니다. 파일 전체의 모든 문제들을 스캔해서 아래와 같은 형식의 텍스트로 추출해주세요.
문제와 풀이에 이미지가 포함되어 있다면 이미지 내용을 텍스트로 묘사해서 포함하거나, 풀 수 있도록 맥락을 제공해주세요.
반드시 각 문제마다 번호, 문제내용, 보기(1,2,3,4), 정답 이 명확하게 구분되어야 합니다.

출력 형식 (예시):
[문제번호]. [문제내용]
1) [보기1]
2) [보기2]
3) [보기3]
4) [보기4]
정답: [정답]
    """
    
    response = model.generate_content([sample_file, prompt])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print(f"\n\nExtracted content has been written to: {output_path}")
    
except Exception as e:
    print(f"An error occurred: {e}")
