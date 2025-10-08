## Overview
EPC Combiner Tool is a desktop application developed in Python for combining EPC (Electronic Product Code) information. It aims to track the production process efficiently.

## Features
- Combine multiple EPC data sources
- Track production stages
- Generate reports
- RFID integration

## Technologies stack

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Qt](https://img.shields.io/badge/Qt-%23217346.svg?style=for-the-badge&logo=Qt&logoColor=white)
![Inno](https://img.shields.io/badge/inno-white?style=for-the-badge)

## Folder structure
```
epc-combiner-tool/
├── .github
│   └── workflows
│       └── release.yaml
├── assets/
├── constants/
├── contexts/
├── database/
├── decorators/
├── events/
├── helpers/
├── i18n/
├── repositories/
├── scripts/
├── services/
├── themes/
├── update/
├── widgets/
├── main.py
├── installer.iss
├── update.bat
├── requirements.txt
├── CHANGELOG.md
├── README.md
├── version.json
├── version_info.txt
├── .gitignore
└── ...
```

## Installation

### 1. Clone the repository:

```bash
git clone https://github.com/quanghiep03198/epc-combiner-tool.git
```

### 2. Navigate to the project directory:

```bash
cd epc-combiner-tool
```

### 3. Create virtual environment:

```bash
python -m venv venv
```

### 4. Activate environment

```bash
venv/Scripts/activate
```


### 5. Install all dependencies packages

```bash
venv/Scripts/python -m pip install -r requirements.txt
```

## Usage

### 1. Run the application:
    
```bash
py main.py
```
### 2. Build application:

**2.1** Show build helpers
```bash
py scripts/build.py -h
```

**2.2** Build application with new updater for specific version
```bash
py scripts/build.py --version <version> --type <developement | release | beta>
```


**Example:** `py scripts/build.py --version v1.0.0 --type release` 


### 3. Create application installer:
    
```bash
iscc "./installer.iss"
```
    

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For any questions or suggestions, please contact [yourname@example.com](mailto:yourname@example.com).
