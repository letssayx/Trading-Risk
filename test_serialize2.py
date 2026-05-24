import uvicorn
from multiprocessing import Process
from backend.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == '__main__':
    p = Process(target=run_server)
    p.start()
    p.join(5) # wait for 5 sec

    # Try fetching data directly from API to see what we get
    import requests
    try:
        res = requests.get("http://127.0.0.1:8000/api/data/view/list?type=dividend&symbol=OFSS")
        print("Status:", res.status_code)
        if res.status_code == 200:
            print("Data length:", len(res.json().get('data', [])))
        else:
            print(res.text)
    except Exception as e:
        print("Error:", e)

    p.terminate()
