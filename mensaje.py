import requests

url = "https://default0b7c0ca9d73a42a2b3bb59b55deb67.a0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/646718e542c641c49f4daed2cd26c0b0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Wm3tX5Neq_YsX7XZhR-Y4fR2w__PGZlmhf3UJwsxrEU"

data = {
    "titulo": "Alta de colaborador",
    "mensaje": "Juan Pérez fue dado de alta"
}

r = requests.post(url, json=data)
print(r.status_code)
