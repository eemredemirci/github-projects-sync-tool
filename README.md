# GitHub Project Management Tool  [EN / TR]

A command-line tool for managing and synchronizing GitHub repositories and GitHub Projects locally. This tool allows you to work with GitHub Projects, issues, milestones, and roadmaps in both online and offline modes.

*GitHub projelerini ve depolarını yerel olarak yönetmek ve senkronize etmek için bir komut satırı aracı. Bu araç, GitHub Projects, sorunlar, kilometre taşları ve yol haritalarıyla hem çevrimiçi hem de çevrimdışı modlarda çalışmanıza olanak tanır.*

## Purpose

This tool bridges the gap between local development environments and GitHub's project management features by:

1. Allowing you to fetch GitHub Projects data and store it locally in both JSON and YAML formats
2. Enabling you to edit project data locally using YAML for better readability
3. Providing synchronization capabilities to keep local and GitHub data consistent
4. Supporting multiple users and repositories

*Bu araç, yerel geliştirme ortamları ile GitHub'ın proje yönetimi özellikleri arasındaki boşluğu şu şekilde kapatır:*

*1. GitHub Projects verilerini çekmenize ve hem JSON hem de YAML formatlarında yerel olarak saklamanıza olanak tanır*
*2. Daha iyi okunabilirlik için YAML kullanarak proje verilerini yerel olarak düzenlemenizi sağlar*
*3. Yerel ve GitHub verilerini tutarlı tutmak için senkronizasyon yetenekleri sunar*
*4. Birden fazla kullanıcı ve depo desteği sağlar*

For a detailed project definition, see [PROJECT_DEFINITION.md](PROJECT_DEFINITION.md).

## Current Status

**Note:** This project is currently in development. The following features are working:

- Fetching GitHub Projects data and storing locally ✅
- Converting between JSON and YAML formats ✅
- User management with token storage ✅
- Interactive CLI interface ✅
- Command-line interface ✅

Features that are still being tested:

- Pushing local changes to GitHub Projects
- Detecting changes between local and GitHub Projects

*Not: Bu proje şu anda geliştirme aşamasındadır. Aşağıdaki özellikler çalışmaktadır:*

*- GitHub Projects verilerini çekme ve yerel olarak saklama ✅*
*- JSON ve YAML formatları arasında dönüştürme ✅*
*- Token depolama ile kullanıcı yönetimi ✅*
*- Etkileşimli CLI arayüzü ✅*
*- Komut satırı arayüzü ✅*

*Hala test edilmekte olan özellikler:*

*- Yerel değişiklikleri GitHub Projects'e gönderme*
*- Yerel ve GitHub Projects arasındaki değişiklikleri tespit etme*

## Features

- **User Management**: Multiple user support with secure token storage
- **Repository Management**: Browse and fetch repository data
- **GitHub Projects Management**: View and manage GitHub Projects
- **Dual-Format Storage**: Work with both JSON and YAML formats
- **Synchronization**: Detect and resolve changes between local and GitHub data
- **Interactive CLI**: Color-coded output and command history tracking

*- **Kullanıcı Yönetimi**: Güvenli token depolama ile çoklu kullanıcı desteği*
*- **Depo Yönetimi**: Depo verilerini görüntüleme ve çekme*
*- **GitHub Projects Yönetimi**: GitHub Projects'i görüntüleme ve yönetme*
*- **Çift Format Depolama**: Hem JSON hem de YAML formatlarıyla çalışma*
*- **Senkronizasyon**: Yerel ve GitHub verileri arasındaki değişiklikleri tespit etme ve çözme*
*- **Etkileşimli CLI**: Renkli çıktı ve komut geçmişi takibi*

## Installation

### Requirements

- Python 3.6+
- pip

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/username/GitHub-Project-Sync-Tool.git
   cd GitHub-Project-Sync-Tool
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode

Interactive mode provides a user-friendly menu interface with color-coded output:

```bash
# Start interactive mode
python run.py
# or
python -m app.main --interactive
```

#### Interactive Mode Features

- **Color-coded output**: 
  - Green for GitHub operations
  - Blue for application operations
  - Yellow for information messages
  - Red for error messages

- **Command history**: Type "history" at any prompt to view recent commands

- **Hierarchical navigation**: Clear menu structure showing the relationship between repositories and GitHub Projects

### Command Line Mode

Command line mode is suitable for scripts and automation:

```bash
# Get help
python -m app.main --help
```

#### User Management

```bash
# Add user
python -m app.main user add <username> <token> --email <email> --name <name>

# List users
python -m app.main user list

# Set default user
python -m app.main user default <username>

# Remove user
python -m app.main user remove <username>
```

#### Repository Operations

```bash
# List repositories
python -m app.main repo list

# Fetch repository data
python -m app.main repo fetch <owner> <repo>
```

#### GitHub Projects Operations

```bash
# List GitHub Projects
python -m app.main project list
python -m app.main project list --repo <repo>

# Fetch GitHub Project data
python -m app.main project fetch <project_id>
```

#### Synchronization Operations

```bash
# List local GitHub Projects
python -m app.main sync list

# Sync from YAML to JSON
python -m app.main sync yaml2json <project_id> <project_name>

# Sync from JSON to YAML
python -m app.main sync json2yaml <project_id> <project_name>

# Check for GitHub Project changes
python -m app.main sync check <project_id> <project_name>

# Check for GitHub changes
python -m app.main sync check-github <project_id> <project_name>

# Send GitHub Project to GitHub
python -m app.main sync push <project_id> <project_name>
```

## Workflow Example

1. **Add a user with GitHub token**:
   ```
   python -m app.main user add myusername mytoken
   ```

2. **Browse repositories**:
   ```
   python -m app.main repo list
   ```

3. **Fetch repository data**:
   ```
   python -m app.main repo fetch myusername myrepo
   ```

4. **List GitHub Projects in the repository**:
   ```
   python -m app.main project list --repo myrepo
   ```

5. **Fetch a GitHub Project**:
   ```
   python -m app.main project fetch 12345
   ```

6. **Edit the YAML file manually** (located at `data/projects/12345_ProjectName/project.yaml`)

7. **Sync changes from YAML to JSON**:
   ```
   python -m app.main sync yaml2json 12345 "Project Name"
   ```

8. **Push changes to GitHub**:
   ```
   python -m app.main sync push 12345 "Project Name"
   ```

## Data Structure

The application stores data in the following directory structure:

```
GitHub-Project-Sync-Tool/
├── data/
│   ├── users/
│   │   └── users.json
│   ├── repositories/
│   │   └── <owner>_<repo>/
│   │       ├── repository.json
│   │       └── repository.yaml
│   ├── projects/
│   │   └── <project_id>_<project_name>/
│   │       ├── project.json
│   │       └── project.yaml
│   └── github_projects/
│       └── <project_id>_<project_name>/
│           └── project.json
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors, please check:
1. Your GitHub token has the required permissions:
   - `repo` - Full control of private repositories
   - `project` - Full control of user projects
   - `read:project` - Read-only access to projects
   - `write:org` - Write access to organization projects

2. The token is correctly entered without any extra spaces

3. Your GitHub account has access to the repositories and projects you're trying to access

### Rate Limiting

GitHub API has rate limits. If you encounter rate limit errors:
1. The tool will automatically wait for rate limits to reset
2. You can reduce the frequency of API calls
3. Consider using a Personal Access Token with higher rate limits

### Other Issues

For other issues, the application will display detailed error messages with traceback information. Please include this information if you need to report a problem.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 
