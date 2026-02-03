{
  "apps": [
    {
      "name": "moltbook-backend",
      "script": "python",
      "args": "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      "cwd": "./backend",
      "instances": 1,
      "autorestart": true,
      "watch": false,
      "max_memory_restart": "500M",
      "env": {
        "PYTHONPATH": ".",
        "PYTHONUNBUFFERED": "1"
      },
      "log_file": "logs/backend.log",
      "error_file": "logs/backend-error.log",
      "out_file": "logs/backend-out.log",
      "time": true
    }
  ]
}
