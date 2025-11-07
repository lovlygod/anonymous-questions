# search_reply.py
import os

def search_reply_in_files():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            if 'Reply' in line:
                                print(f"{file_path}:{i}: {line.strip()}")
                except:
                    try:
                        with open(file_path, 'r', encoding='cp1251') as f:
                            for i, line in enumerate(f, 1):
                                if 'Reply' in line:
                                    print(f"{file_path}:{i}: {line.strip()}")
                    except:
                        pass

if __name__ == "__main__":
    search_reply_in_files()