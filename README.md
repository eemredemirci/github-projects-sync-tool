# GitHub Project Management Tool

A command-line tool for managing and synchronizing GitHub repositories and **GitHub Projects** locally. It bridges the GitHub REST API, local **JSON/YAML** storage, change review, and optional sync back to GitHub (issues, milestones, project fields).

*GitHub REST API ile yerel JSON/YAML depolama, değişiklik incelemesi ve isteğe bağlı olarak GitHub’a geri senkronizasyon (issue, milestone, proje alanları) sağlayan bir CLI aracı.*

**Repository:** [eemredemirci/github-projects-sync-tool](https://github.com/eemredemirci/github-projects-sync-tool)

## Purpose

This tool bridges the gap between local development environments and GitHub's project management features by:

1. Allowing you to fetch GitHub Projects data and store it locally in both JSON and YAML formats
2. Enabling you to edit project data locally using YAML for better readability
3. Providing synchronization capabilities to keep local and GitHub data consistent
4. Supporting multiple users and repositories
5. Offering advanced change tracking for safe synchronization with GitHub

*Bu araç, yerel geliştirme ortamları ile GitHub'ın proje yönetimi özellikleri arasındaki boşluğu şu şekilde kapatır:*

*1. GitHub Projects verilerini çekmenize ve hem JSON hem de YAML formatlarında yerel olarak saklamanıza olanak tanır*
*2. Daha iyi okunabilirlik için YAML kullanarak proje verilerini yerel olarak düzenlemenizi sağlar*
*3. Yerel ve GitHub verilerini tutarlı tutmak için senkronizasyon yetenekleri sunar*
*4. Birden fazla kullanıcı ve depo desteği sağlar*
*5. GitHub ile güvenli senkronizasyon için gelişmiş değişiklik takibi sunar*

For a detailed project definition, see [PROJECT_DEFINITION.md](PROJECT_DEFINITION.md).

## Current Status

**Note:** This project is currently in development. The following features are working:

- Fetching GitHub Projects data and storing locally ✅
- Converting between JSON and YAML formats ✅
- User management with token storage ✅
- Interactive CLI interface ✅
- Command-line interface ✅
- Change tracking and syncing to GitHub ✅

*Not: Bu proje şu anda geliştirme aşamasındadır. Aşağıdaki özellikler çalışmaktadır:*

*- GitHub Projects verilerini çekme ve yerel olarak saklama ✅*
*- JSON ve YAML formatları arasında dönüştürme ✅*
*- Token depolama ile kullanıcı yönetimi ✅*
*- Etkileşimli CLI arayüzü ✅*
*- Komut satırı arayüzü ✅*
*- Değişiklik takibi ve GitHub'a senkronizasyon ✅*

## Features

- **User Management**: Multiple user support with secure token storage
- **Repository Management**: Browse and fetch repository data
- **GitHub Projects Management**: View and manage GitHub Projects
- **Dual-Format Storage**: Work with both JSON and YAML formats
- **Synchronization**: Detect and resolve changes between local and GitHub data
- **Interactive CLI**: Color-coded output and command history tracking
- **Change Tracking System**: Advanced system to detect, review, and approve changes before sending to GitHub

*- **Kullanıcı Yönetimi**: Güvenli token depolama ile çoklu kullanıcı desteği*
*- **Depo Yönetimi**: Depo verilerini görüntüleme ve çekme*
*- **GitHub Projects Yönetimi**: GitHub Projects'i görüntüleme ve yönetme*
*- **Çift Format Depolama**: Hem JSON hem de YAML formatlarıyla çalışma*
*- **Senkronizasyon**: Yerel ve GitHub verileri arasındaki değişiklikleri tespit etme ve çözme*
*- **Etkileşimli CLI**: Renkli çıktı ve komut geçmişi takibi*
*- **Değişiklik Takip Sistemi**: GitHub'a göndermeden önce değişiklikleri tespit etme, inceleme ve onaylama için gelişmiş sistem*

## Installation

### Requirements

- Python 3.8+ (önerilir)
- pip

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/eemredemirci/github-projects-sync-tool.git
   cd github-projects-sync-tool
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

### Change Tracking System

The tool includes a comprehensive change tracking system that allows you to:

1. **Detect changes** between original GitHub data and your local modifications
2. **Review changes** before sending them to GitHub
3. **Approve or reject** individual changes or in bulk
4. **Track operations** for transparency and auditability
5. **Synchronize safely** with GitHub

#### Working with Local Files

You can directly edit files in your file system:

- **Adding new issues**: Create a new file named `issue_X.json` or `issue_X.yaml` in the appropriate milestone directory
- **Updating issues**: Edit the existing issue files
- **Deleting issues**: Remove the issue files
- **Adding milestones**: Create a new directory under the `milestones/` folder with appropriate files
- **Editing milestones**: Update the milestone files

After making changes to your local files, use the "Manage Changes & Sync to GitHub" option in the project menu to detect, review, and approve these changes.

### Command Line Mode

Command line mode is suitable for scripts and automation:

```bash
# Get help
python -m app.main --help
```

#### User Management

```bash
# Add user
python -m app.main user add <username> <token> --email <email> --name <n>

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

# Manage changes and synchronize with GitHub
python -m app.main sync changes <project_id> <project_name>

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

6. **Edit the local files manually**:
   - Add/edit/delete issues in `data/projects/12345_ProjectName/milestones/`
   - Update milestone information

7. **Detect and review changes**:
   ```
   python -m app.main sync changes 12345 "Project Name"
   ```

8. **Push approved changes to GitHub**:
   ```
   python -m app.main sync push 12345 "Project Name"
   ```

## Data Structure

The application stores data in the following directory structure:

```
github-projects-sync-tool/
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
│   │       ├── project.yaml
│   │       ├── .cache/
│   │       │   └── original_state.json
│   │       ├── .pending/
│   │       │   └── github_operations.json
│   │       ├── logs/
│   │       │   └── sync_YYYYMMDD_HHMMSS.log
│   │       ├── sync_history/
│   │       │   └── YYYYMMDD_HHMMSS_sync_results.json
│   │       └── milestones/
│   │           ├── milestone_name/
│   │           │   ├── milestone_name.json
│   │           │   ├── issue_1.json
│   │           │   ├── issue_2.json
│   │           │   └── issue_3_parent/
│   │           │       ├── issue_4.json
│   │           │       └── issue_5.json
│   │           └── no_milestone/
│   │               ├── issue_6.json
│   │               └── issue_7.json
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