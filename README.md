# 📅 Agenda SC – Sistema de Compromissos Regionais

[![Status](https://img.shields.io/badge/status-concluído-brightgreen?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat-square&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![FullCalendar](https://img.shields.io/badge/FullCalendar-6.1-0A7E8C?style=flat-square&logo=fullcalendar&logoColor=white)](https://fullcalendar.io/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

Sistema web para gerenciamento de compromissos entre uma administração central e suas unidades regionais (cidades de Santa Catarina).

---

## ✨ Funcionalidades

- 🔐 **Autenticação de usuários** (admin e usuários comuns)
- 👥 **Painel do Administrador**
  - Cadastrar, editar e excluir compromissos por cidade
  - Visualizar calendário mensal interativo
  - Gerenciar usuários (criar, listar, remover)
  - Dashboard com estatísticas e cidades ativas
  - Exportar agenda em CSV
- 👤 **Painel do Usuário**
  - Visualizar compromissos da sua cidade ou filtrar por qualquer cidade
  - Calendário com feriados nacionais
  - Lista lateral dos próximos compromissos
  - Fazer check‑in (confirmar presença)
  - Exportar agenda filtrada
- 🎨 **Interface moderna** com Bootstrap 5, ícones e calendário interativo (FullCalendar)

---

## 🛠️ Tecnologias

- **Python 3.10+** com **Flask** (backend)
- **SQLite** (banco de dados leve)
- **Bootstrap 5** e **FullCalendar** (frontend)
- **Flask-Login** e **Werkzeug** (autenticação e segurança)

---

## 🚀 Como Executar

1. Clone o repositório:

```bash
git clone https://github.com/douglasbecker404/Calendario.git
cd Calendario-Grupo
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute a aplicação:

```bash
python app.py
```

5. Acesse no navegador: `http://localhost:5000`

---

## 👤 Usuários de teste

| Tipo | Usuário | Senha |
|------|---------|-------|
| Admin | `admin` | `admin123` |

---

## 📂 Estrutura do Projeto

```bash
├── app.py
├── requirements.txt
├── .gitignore
├── static/
│   └── css/
│       └── style.css
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── cadastro.html
│   ├── admin.html
│   ├── usuario.html
│   └── perfil.html
└── README.md
```

---

## 📝 Licença

Projeto desenvolvido para fins acadêmicos. Sinta‑se à vontade para estudar e modificar.

---

Feito com ❤️ para a disciplina de DevOps.
```