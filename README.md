# Introduction 
User web portal for AWX

# Prerequisites
`pip3` must be installed on the machine.

## Environment variables

| Name | Description | Default value |
|-|-|-|
| **AWX_URL** | AWX base url | |
| **AWX_TOKEN** | AWX User Token with Write permissions | |

# Build and Test
Run the following commands (warning : use _pip_ and _python_ if running on Windows)
```
pip3 install -r requirements.txt
python3 app.py
```
