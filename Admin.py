import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import os
import json
import hashlib
from PIL import Image, ImageTk  # Para ícones (opcional, instale com pip install Pillow)

# ==================== CONFIGURAÇÃO DE ESTILO ====================
def configurar_estilo():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=('Segoe UI', 10), padding=6)
    style.configure('TLabel', font=('Segoe UI', 10))
    style.configure('TEntry', padding=5)
    style.configure('TCombobox', padding=5)
    style.map('TButton', background=[('active', '#45a049')])

# ==================== GERENCIADOR DE DADOS ====================
class DataManager:
    AGENDA_FILE = 'agenda.json'
    USUARIOS_FILE = 'usuarios.json'

    @staticmethod
    def carregar_agenda():
        if os.path.exists(DataManager.AGENDA_FILE):
            with open(DataManager.AGENDA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @staticmethod
    def salvar_agenda(agenda):
        with open(DataManager.AGENDA_FILE, 'w', encoding='utf-8') as f:
            json.dump(agenda, f, ensure_ascii=False, indent=2)

    @staticmethod
    def carregar_usuarios():
        if os.path.exists(DataManager.USUARIOS_FILE):
            with open(DataManager.USUARIOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Estrutura inicial com admin e alguns usuários fixos
        usuarios = {
            "admin": {
                "senha_hash": hashlib.sha256("admin123".encode()).hexdigest(),
                "tipo": "ADM"
            },
            "portouniao": {
                "senha_hash": hashlib.sha256("1234".encode()).hexdigest(),
                "tipo": "Usuário",
                "cidade": "Porto União"
            },
            "florianopolis": {
                "senha_hash": hashlib.sha256("1234".encode()).hexdigest(),
                "tipo": "Usuário",
                "cidade": "Florianópolis"
            },
            "joinville": {
                "senha_hash": hashlib.sha256("1234".encode()).hexdigest(),
                "tipo": "Usuário",
                "cidade": "Joinville"
            },
            "blumenau": {
                "senha_hash": hashlib.sha256("1234".encode()).hexdigest(),
                "tipo": "Usuário",
                "cidade": "Blumenau"
            },
            "chapeco": {
                "senha_hash": hashlib.sha256("1234".encode()).hexdigest(),
                "tipo": "Usuário",
                "cidade": "Chapecó"
            }
        }
        DataManager.salvar_usuarios(usuarios)
        return usuarios

    @staticmethod
    def salvar_usuarios(usuarios):
        with open(DataManager.USUARIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=2)

# ==================== WIDGET AUTOCOMPLETE ====================
class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, parent, values, **kwargs):
        super().__init__(parent, values=values, **kwargs)
        self._values = values
        self.bind('<KeyRelease>', self._on_keyrelease)

    def _on_keyrelease(self, event):
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Return'):
            return
        typed = self.get().lower()
        filtered = [v for v in self._values if typed in v.lower()]
        self['values'] = filtered
        if filtered:
            self.event_generate('<Down>')

# ==================== JANELA DE DETALHES DO DIA ====================
class DetalhesDiaWindow(tk.Toplevel):
    def __init__(self, parent, data_iso, compromissos, callback_atualizar):
        super().__init__(parent)
        self.data_iso = data_iso
        self.compromissos = compromissos
        self.callback_atualizar = callback_atualizar
        self.title(f"Compromissos - {self._formatar_data(data_iso)}")
        self.geometry("500x450")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg='#f0f0f0')

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text=f"Compromissos em {self._formatar_data(data_iso)}",
                  font=('Segoe UI', 12, 'bold')).pack(pady=(0,10))

        if not self.compromissos:
            ttk.Label(frame, text="Nenhum compromisso neste dia.").pack()
            ttk.Button(frame, text="Fechar", command=self.destroy).pack(pady=20)
            return

        # Frame com scroll
        canvas = tk.Canvas(frame, borderwidth=0, highlightthickness=0, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        self.scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0,0), window=self.scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.criar_lista_compromissos()

        ttk.Button(frame, text="Fechar", command=self.destroy).pack(pady=10)

    def _formatar_data(self, data_iso):
        dt = datetime.strptime(data_iso, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")

    def criar_lista_compromissos(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for comp in sorted(self.compromissos, key=lambda x: x['hora']):
            frame_comp = ttk.Frame(self.scroll_frame, relief='solid', borderwidth=1, padding=5)
            frame_comp.pack(fill='x', pady=3)

            info = f"{comp['hora']} - {comp['descricao']}"
            status = "✅ Confirmado" if comp.get('checkin', False) else "⏳ Pendente"
            cor_fundo = '#d4edda' if comp.get('checkin', False) else '#fff3cd'

            frame_comp.configure(style='Card.TFrame')
            ttk.Label(frame_comp, text=info, font=('Segoe UI', 10)).pack(side='left', padx=5)
            lbl_status = ttk.Label(frame_comp, text=status, font=('Segoe UI', 9, 'bold'))
            lbl_status.pack(side='left', padx=10)

            if not comp.get('checkin', False):
                btn = ttk.Button(frame_comp, text="✔ Check-in",
                                 command=lambda c=comp: self.realizar_checkin(c))
                btn.pack(side='right', padx=5)

    def realizar_checkin(self, compromisso):
        compromisso['checkin'] = True
        self.criar_lista_compromissos()
        if self.callback_atualizar:
            self.callback_atualizar()

# ==================== JANELA DO CALENDÁRIO ====================
class CalendarioWindow(tk.Toplevel):
    def __init__(self, parent, cidade, compromissos, callback_global=None):
        super().__init__(parent)
        self.title(f"Agenda - {cidade}")
        self.geometry("700x650")
        self.resizable(True, True)
        self.cidade = cidade
        self.compromissos = compromissos
        self.callback_global = callback_global
        self.hoje = datetime.now()
        self.ano_atual = self.hoje.year
        self.mes_atual = self.hoje.month

        self.header = ttk.Frame(self, padding=10)
        self.header.pack(fill='x')

        self.btn_anterior = ttk.Button(self.header, text="◀", command=self.mes_anterior)
        self.btn_anterior.pack(side='left', padx=5)
        self.lbl_mes = ttk.Label(self.header, text="", font=('Segoe UI', 14, 'bold'))
        self.lbl_mes.pack(side='left', expand=True)
        self.btn_proximo = ttk.Button(self.header, text="▶", command=self.proximo_mes)
        self.btn_proximo.pack(side='right', padx=5)

        self.frame_calendario = ttk.Frame(self, padding=10)
        self.frame_calendario.pack(fill='both', expand=True)

        self.atualizar_calendario()

    def obter_compromissos_do_dia(self, data_iso):
        return [c for c in self.compromissos if c['data_iso'] == data_iso]

    def atualizar_calendario(self):
        for widget in self.frame_calendario.winfo_children():
            widget.destroy()

        self.lbl_mes.config(text=f"{calendar.month_name[self.mes_atual]} de {self.ano_atual}")

        dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
        for i, dia in enumerate(dias_semana):
            lbl = ttk.Label(self.frame_calendario, text=dia, font=('Segoe UI', 9, 'bold'),
                            relief='ridge', anchor='center', padding=5)
            lbl.grid(row=0, column=i, padx=1, pady=1, sticky='nsew')

        cal = calendar.monthcalendar(self.ano_atual, self.mes_atual)
        for r, semana in enumerate(cal):
            for c, dia in enumerate(semana):
                if dia != 0:
                    data_iso = f"{self.ano_atual:04d}-{self.mes_atual:02d}-{dia:02d}"
                    comps_dia = self.obter_compromissos_do_dia(data_iso)

                    frame_dia = tk.Frame(self.frame_calendario, relief='ridge', borderwidth=1,
                                         width=90, height=90, bg='white')
                    frame_dia.grid(row=r+1, column=c, padx=1, pady=1, sticky='nsew')
                    frame_dia.pack_propagate(False)

                    # Destacar dia atual
                    if (self.ano_atual, self.mes_atual, dia) == (self.hoje.year, self.hoje.month, self.hoje.day):
                        frame_dia.configure(bg='#cce5ff')  # azul claro

                    # Destacar dias com compromissos
                    if comps_dia:
                        frame_dia.configure(bg='#d4edda')  # verde claro

                    lbl_num = tk.Label(frame_dia, text=str(dia), font=('Segoe UI', 9, 'bold'),
                                       fg='red' if (self.ano_atual, self.mes_atual, dia) == (self.hoje.year, self.hoje.month, self.hoje.day) else 'black',
                                       bg=frame_dia['bg'])
                    lbl_num.pack(anchor='nw', padx=2, pady=2)

                    if comps_dia:
                        comps_ordenados = sorted(comps_dia, key=lambda x: x['hora'])
                        max_exibir = 3
                        for i, comp in enumerate(comps_ordenados[:max_exibir]):
                            hora = comp['hora']
                            checkin = comp.get('checkin', False)
                            texto = f"{hora}"
                            if i == max_exibir-1 and len(comps_ordenados) > max_exibir:
                                texto += " ..."
                            cor_texto = 'green' if checkin else 'black'
                            lbl_comp = tk.Label(frame_dia, text=texto, font=('Segoe UI', 7),
                                                fg=cor_texto, bg=frame_dia['bg'], anchor='w')
                            lbl_comp.pack(anchor='w', padx=2)

                    # Bind para abrir popup
                    for widget in [frame_dia, lbl_num] + list(frame_dia.winfo_children()):
                        widget.bind('<Button-1>', lambda e, d=data_iso: self._abrir_popup(d))
                else:
                    lbl_vazio = tk.Label(self.frame_calendario, text='', relief='ridge', bg='lightgray')
                    lbl_vazio.grid(row=r+1, column=c, padx=1, pady=1, sticky='nsew')

        # Configurar pesos para redimensionamento
        for i in range(7):
            self.frame_calendario.columnconfigure(i, weight=1)
        for i in range(len(cal)+1):
            self.frame_calendario.rowconfigure(i, weight=1)

    def _abrir_popup(self, data_iso):
        comps = self.obter_compromissos_do_dia(data_iso)
        DetalhesDiaWindow(self, data_iso, comps,
                         callback_atualizar=lambda: [self.atualizar_calendario(),
                                                     self.callback_global() if self.callback_global else None])

    def mes_anterior(self):
        if self.mes_atual == 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        else:
            self.mes_atual -= 1
        self.atualizar_calendario()

    def proximo_mes(self):
        if self.mes_atual == 12:
            self.mes_atual = 1
            self.ano_atual += 1
        else:
            self.mes_atual += 1
        self.atualizar_calendario()

# ==================== SISTEMA PRINCIPAL ====================
class SistemaAgenda:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Agenda - SC")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        configurar_estilo()

        self.agenda = DataManager.carregar_agenda()
        self.usuarios = DataManager.carregar_usuarios()
        self.cidades_sc = [
            "Abdon Batista", "Abelardo Luz", "Agrolândia", "Agronômica", "Água Doce",
            "Águas de Chapecó", "Águas Frias", "Águas Mornas", "Alfredo Wagner", "Alto Bela Vista",
            "Anchieta", "Angelina", "Anita Garibaldi", "Anitápolis", "Antônio Carlos",
            "Apiúna", "Arabutã", "Araquari", "Araranguá", "Armazém",
            "Arroio Trinta", "Arvoredo", "Ascurra", "Atalanta", "Aurora",
            "Balneário Arroio do Silva", "Balneário Barra do Sul", "Balneário Camboriú", "Balneário Gaivota", "Balneário Piçarras",
            "Balneário Rincão", "Bandeirante", "Barra Bonita", "Barra Velha", "Bela Vista do Toldo",
            "Belmonte", "Benedito Novo", "Biguaçu", "Blumenau", "Bocaina do Sul",
            "Bom Jardim da Serra", "Bom Jesus", "Bom Jesus do Oeste", "Bom Retiro", "Bombinhas",
            "Botuverá", "Braço do Norte", "Braço do Trombudo", "Brunópolis", "Brusque",
            "Caçador", "Caibi", "Calmon", "Camboriú", "Campo Alegre",
            "Campo Belo do Sul", "Campo Erê", "Campos Novos", "Canelinha", "Canoinhas",
            "Capão Alto", "Capinzal", "Capivari de Baixo", "Catanduvas", "Caxambu do Sul",
            "Celso Ramos", "Cerro Negro", "Chapadão do Lageado", "Chapecó", "Cocal do Sul",
            "Concórdia", "Cordilheira Alta", "Coronel Freitas", "Coronel Martins", "Correia Pinto",
            "Corupá", "Criciúma", "Cunha Porã", "Cunhataí", "Curitibanos",
            "Descanso", "Dionísio Cerqueira", "Dona Emma", "Doutor Pedrinho", "Entre Rios",
            "Ermo", "Erval Velho", "Faxinal dos Guedes", "Flor do Sertão", "Florianópolis",
            "Formosa do Sul", "Forquilhinha", "Fraiburgo", "Frei Rogério", "Galvão",
            "Garopaba", "Garuva", "Gaspar", "Governador Celso Ramos", "Grão Pará",
            "Gravatal", "Guabiruba", "Guaraciaba", "Guaramirim", "Guarujá do Sul",
            "Guatambú", "Herval d'Oeste", "Ibiam", "Ibicaré", "Ibirama",
            "Içara", "Ilhota", "Imaruí", "Imbituba", "Imbuia",
            "Indaial", "Iomerê", "Ipira", "Iporã do Oeste", "Ipuaçu",
            "Ipumirim", "Iraceminha", "Irani", "Irati", "Irineópolis",
            "Itá", "Itaiópolis", "Itajaí", "Itapema", "Itapiranga",
            "Itapoá", "Ituporanga", "Jaborá", "Jacinto Machado", "Jaguaruna",
            "Jaraguá do Sul", "Jardinópolis", "Joaçaba", "Joinville", "José Boiteux",
            "Jupiá", "Lacerdópolis", "Lages", "Laguna", "Lajeado Grande",
            "Laurentino", "Lauro Müller", "Lebon Régis", "Leoberto Leal", "Lindóia do Sul",
            "Lontras", "Luiz Alves", "Luzerna", "Macieira", "Mafra",
            "Major Gercino", "Major Vieira", "Maracajá", "Maravilha", "Marema",
            "Massaranduba", "Matos Costa", "Meleiro", "Mirim Doce", "Modelo",
            "Mondaí", "Monte Carlo", "Monte Castelo", "Morro da Fumaça", "Morro Grande",
            "Navegantes", "Nova Erechim", "Nova Itaberaba", "Nova Trento", "Nova Veneza",
            "Novo Horizonte", "Orleans", "Otacílio Costa", "Ouro", "Ouro Verde",
            "Paial", "Painel", "Palhoça", "Palma Sola", "Palmeira",
            "Palmitos", "Papanduva", "Paraíso", "Passo de Torres", "Passos Maia",
            "Paulo Lopes", "Pedras Grandes", "Penha", "Peritiba", "Pescaria Brava",
            "Petrolândia", "Pinhalzinho", "Pinheiro Preto", "Piratuba", "Planalto Alegre",
            "Pomerode", "Ponte Alta", "Ponte Alta do Norte", "Ponte Serrada", "Porto Belo",
            "Porto União", "Pouso Redondo", "Praia Grande", "Presidente Castello Branco", "Presidente Getúlio",
            "Presidente Nereu", "Princesa", "Quilombo", "Rancho Queimado", "Rio das Antas",
            "Rio do Campo", "Rio do Oeste", "Rio do Sul", "Rio dos Cedros", "Rio Fortuna",
            "Rio Negrinho", "Rio Rufino", "Riqueza", "Rodeio", "Romelândia",
            "Salete", "Saltinho", "Salto Veloso", "Sangão", "Santa Cecília",
            "Santa Helena", "Santa Rosa de Lima", "Santa Rosa do Sul", "Santa Terezinha", "Santa Terezinha do Progresso",
            "Santiago do Sul", "Santo Amaro da Imperatriz", "São Bento do Sul", "São Bernardino", "São Bonifácio",
            "São Carlos", "São Cristóvão do Sul", "São Domingos", "São Francisco do Sul", "São João Batista",
            "São João do Itaperiú", "São João do Oeste", "São João do Sul", "São Joaquim", "São José",
            "São José do Cedro", "São José do Cerrito", "São Lourenço do Oeste", "São Ludgero", "São Martinho",
            "São Miguel da Boa Vista", "São Miguel do Oeste", "São Pedro de Alcântara", "Saudades", "Schroeder",
            "Seara", "Serra Alta", "Siderópolis", "Sombrio", "Sul Brasil",
            "Taió", "Tangará", "Tigrinhos", "Tijucas", "Timbé do Sul",
            "Timbó", "Timbó Grande", "Três Barras", "Treviso", "Treze de Maio",
            "Treze Tílias", "Trombudo Central", "Tubarão", "Tunápolis", "Turvo",
            "União do Oeste", "Urubici", "Urupema", "Urussanga", "Vargeão",
            "Vargem", "Vargem Bonita", "Vidal Ramos", "Videira", "Vitor Meireles",
            "Witmarsum", "Xanxerê", "Xavantina", "Xaxim", "Zortéa"
        ]

        self.carregar_dados_exemplo()
        self.criar_tela_login()

    # ---------- DADOS DE EXEMPLO ----------
    def carregar_dados_exemplo(self):
        # Só insere exemplos se a agenda estiver vazia
        if not self.agenda:
            hoje = datetime.now().strftime("%Y-%m-%d")
            amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            depois = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            exemplos = {
                "Porto União": [
                    {"data_iso": hoje, "hora": "09:00", "descricao": "Reunião com fornecedores", "checkin": False},
                    {"data_iso": hoje, "hora": "14:00", "descricao": "Visita técnica à fábrica", "checkin": False},
                    {"data_iso": amanha, "hora": "10:00", "descricao": "Treinamento equipe", "checkin": False}
                ],
                "Florianópolis": [
                    {"data_iso": hoje, "hora": "11:00", "descricao": "Reunião diretoria", "checkin": False},
                    {"data_iso": amanha, "hora": "15:00", "descricao": "Palestra inovação", "checkin": False}
                ],
                "Joinville": [
                    {"data_iso": hoje, "hora": "08:00", "descricao": "Feira industrial", "checkin": False}
                ]
            }
            for cidade, comps in exemplos.items():
                self.agenda[cidade] = comps
            DataManager.salvar_agenda(self.agenda)

    # ---------- MÉTODOS AUXILIARES ----------
    def limpar_tela(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def salvar_tudo(self):
        DataManager.salvar_agenda(self.agenda)
        DataManager.salvar_usuarios(self.usuarios)

    # ==================== TELAS DE LOGIN ====================
    def criar_tela_login(self):
        self.limpar_tela()
        self.root.geometry("500x400")
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        ttk.Label(frame, text="Acesso ao Sistema", font=('Segoe UI', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0,20))

        ttk.Label(frame, text="Tipo de acesso:").grid(row=1, column=0, sticky='w', pady=5)
        self.tipo_var = tk.StringVar(value='Usuário')
        ttk.Radiobutton(frame, text="Administrador", variable=self.tipo_var, value='ADM').grid(row=1, column=1, sticky='w')
        ttk.Radiobutton(frame, text="Usuário", variable=self.tipo_var, value='Usuário').grid(row=2, column=1, sticky='w')

        ttk.Label(frame, text="Usuário:").grid(row=3, column=0, sticky='w', pady=(15,0))
        self.entry_usuario = ttk.Entry(frame, width=30)
        self.entry_usuario.grid(row=3, column=1, pady=(15,0))

        ttk.Label(frame, text="Senha:").grid(row=4, column=0, sticky='w', pady=5)
        self.entry_senha = ttk.Entry(frame, width=30, show='*')
        self.entry_senha.grid(row=4, column=1, pady=5)

        botoes_frame = ttk.Frame(frame)
        botoes_frame.grid(row=5, column=0, columnspan=2, pady=25)
        ttk.Button(botoes_frame, text="Entrar", command=self.verificar_login).pack(side='left', padx=5)
        ttk.Button(botoes_frame, text="Cadastrar-se", command=self.abrir_tela_cadastro).pack(side='left', padx=5)

    def verificar_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()
        tipo_selecionado = self.tipo_var.get()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha todos os campos.")
            return

        if usuario not in self.usuarios:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return

        dados = self.usuarios[usuario]
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()

        if dados['senha_hash'] != senha_hash:
            messagebox.showerror("Erro", "Senha incorreta.")
            return

        if dados['tipo'] != tipo_selecionado:
            messagebox.showerror("Erro", f"Usuário '{usuario}' não é do tipo {tipo_selecionado}.")
            return

        messagebox.showinfo("Sucesso", f"Bem-vindo(a), {usuario}!")
        if dados['tipo'] == 'ADM':
            self.painel_admin()
        else:
            cidade = dados.get('cidade', None)
            self.painel_usuario(cidade_fixa=cidade)

    # ==================== CADASTRO DE USUÁRIO COMUM ====================
    def abrir_tela_cadastro(self):
        janela = tk.Toplevel(self.root)
        janela.title("Cadastrar novo usuário")
        janela.geometry("400x300")
        janela.resizable(False, False)
        janela.grab_set()

        frame = ttk.Frame(janela, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Criar conta de Usuário", font=('Segoe UI', 12, 'bold')).pack(pady=(0,10))
        ttk.Label(frame, text="Nome de usuário:").pack(anchor='w')
        entry_usuario = ttk.Entry(frame, width=30)
        entry_usuario.pack(pady=2)
        ttk.Label(frame, text="Senha:").pack(anchor='w')
        entry_senha = ttk.Entry(frame, width=30, show='*')
        entry_senha.pack(pady=2)
        ttk.Label(frame, text="Confirmar senha:").pack(anchor='w')
        entry_confirma = ttk.Entry(frame, width=30, show='*')
        entry_confirma.pack(pady=2)

        # Cidade (opcional para usuário comum)
        ttk.Label(frame, text="Cidade (opcional):").pack(anchor='w', pady=(10,0))
        combo_cidade = AutocompleteCombobox(frame, self.cidades_sc, width=28)
        combo_cidade.pack(pady=2)

        def realizar_cadastro():
            user = entry_usuario.get().strip()
            senha = entry_senha.get().strip()
            confirma = entry_confirma.get().strip()
            cidade = combo_cidade.get()

            if not user or not senha or not confirma:
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios.", parent=janela)
                return
            if user in self.usuarios:
                messagebox.showerror("Erro", "Nome de usuário já existe.", parent=janela)
                return
            if senha != confirma:
                messagebox.showerror("Erro", "Senhas não conferem.", parent=janela)
                return

            self.usuarios[user] = {
                'senha_hash': hashlib.sha256(senha.encode()).hexdigest(),
                'tipo': 'Usuário',
                'cidade': cidade if cidade else None
            }
            self.salvar_tudo()
            messagebox.showinfo("Sucesso", "Conta criada com sucesso!", parent=janela)
            janela.destroy()

        ttk.Button(frame, text="Cadastrar", command=realizar_cadastro).pack(pady=20)

    # ==================== PAINEL ADMINISTRADOR ====================
    def painel_admin(self):
        self.limpar_tela()
        self.root.geometry("900x650")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        # Aba Compromissos
        tab_compromissos = ttk.Frame(notebook)
        notebook.add(tab_compromissos, text='Compromissos')

        # Aba Gerenciar Usuários
        tab_usuarios = ttk.Frame(notebook)
        notebook.add(tab_usuarios, text='Gerenciar Usuários')

        # ----- Aba Compromissos -----
        frame = ttk.Frame(tab_compromissos, padding=15)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Painel do Administrador", font=('Segoe UI', 14, 'bold')).pack(pady=5)

        # Seleção de cidade
        ttk.Label(frame, text="Cidade:").pack(anchor='w')
        self.cidade_var = tk.StringVar()
        self.combo_cidade = AutocompleteCombobox(frame, self.cidades_sc, textvariable=self.cidade_var, width=40)
        self.combo_cidade.pack(fill='x', pady=2)
        self.combo_cidade.set("Selecione uma cidade")

        # Campos de data, hora e descrição
        campos_frame = ttk.Frame(frame)
        campos_frame.pack(pady=10)

        ttk.Label(campos_frame, text="Data (DD/MM/AAAA):").grid(row=0, column=0, sticky='w')
        self.entry_data = ttk.Entry(campos_frame, width=12)
        self.entry_data.grid(row=0, column=1, padx=5)
        ttk.Label(campos_frame, text="Hora (HH:MM):").grid(row=0, column=2, sticky='w')
        self.entry_hora = ttk.Entry(campos_frame, width=8)
        self.entry_hora.grid(row=0, column=3, padx=5)

        ttk.Label(frame, text="Descrição:").pack(anchor='w')
        self.entry_desc = ttk.Entry(frame, width=50)
        self.entry_desc.pack(fill='x', pady=2)

        botoes_frame = ttk.Frame(frame)
        botoes_frame.pack(pady=10)
        ttk.Button(botoes_frame, text="➕ Adicionar", command=self.adicionar_compromisso).pack(side='left', padx=3)
        ttk.Button(botoes_frame, text="✏️ Editar", command=self.editar_compromisso).pack(side='left', padx=3)
        ttk.Button(botoes_frame, text="🗑️ Remover", command=self.remover_compromisso).pack(side='left', padx=3)
        ttk.Button(botoes_frame, text="✔ Check-in", command=self.checkin_admin).pack(side='left', padx=3)
        ttk.Button(botoes_frame, text="📅 Calendário", command=self.abrir_calendario_admin).pack(side='left', padx=3)

        # Tabela de compromissos
        ttk.Label(frame, text="Compromissos da cidade:").pack(anchor='w', pady=(10,0))
        colunas = ('Data', 'Hora', 'Descrição', 'Status')
        self.tree = ttk.Treeview(frame, columns=colunas, show='headings', height=8)
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120 if col != 'Descrição' else 300)
        self.tree.pack(fill='both', expand=True, pady=5)

        self.combo_cidade.bind('<<ComboboxSelected>>', lambda e: self.atualizar_tabela_admin())

        ttk.Button(frame, text="Logout", command=self.criar_tela_login).pack(pady=10)

        # ----- Aba Gerenciar Usuários -----
        frame_usuarios = ttk.Frame(tab_usuarios, padding=15)
        frame_usuarios.pack(fill='both', expand=True)

        ttk.Label(frame_usuarios, text="Gerenciar Usuários", font=('Segoe UI', 14, 'bold')).pack(pady=5)

        # Formulário de cadastro pelo admin
        form_frame = ttk.LabelFrame(frame_usuarios, text="Cadastrar novo usuário", padding=10)
        form_frame.pack(fill='x', pady=10)

        ttk.Label(form_frame, text="Usuário:").grid(row=0, column=0, sticky='w', pady=2)
        self.novo_user_entry = ttk.Entry(form_frame, width=20)
        self.novo_user_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(form_frame, text="Senha:").grid(row=0, column=2, sticky='w', pady=2)
        self.novo_senha_entry = ttk.Entry(form_frame, width=20, show='*')
        self.novo_senha_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(form_frame, text="Cidade:").grid(row=1, column=0, sticky='w', pady=2)
        self.novo_cidade_combo = AutocompleteCombobox(form_frame, self.cidades_sc, width=18)
        self.novo_cidade_combo.grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(form_frame, text="Tipo:").grid(row=1, column=2, sticky='w', pady=2)
        self.novo_tipo_var = tk.StringVar(value='Usuário')
        ttk.Combobox(form_frame, textvariable=self.novo_tipo_var, values=['Usuário', 'ADM'], state='readonly', width=18).grid(row=1, column=3, padx=5, pady=2)

        ttk.Button(form_frame, text="Cadastrar", command=self.cadastrar_usuario_admin).grid(row=2, column=0, columnspan=4, pady=10)

        # Lista de usuários
        ttk.Label(frame_usuarios, text="Usuários cadastrados:").pack(anchor='w', pady=(10,0))
        colunas_usr = ('Usuário', 'Tipo', 'Cidade')
        self.tree_usuarios = ttk.Treeview(frame_usuarios, columns=colunas_usr, show='headings', height=6)
        for col in colunas_usr:
            self.tree_usuarios.heading(col, text=col)
            self.tree_usuarios.column(col, width=150)
        self.tree_usuarios.pack(fill='both', expand=True, pady=5)
        self.atualizar_lista_usuarios()

        ttk.Button(frame_usuarios, text="Excluir usuário selecionado", command=self.excluir_usuario_admin).pack(pady=10)

    def cadastrar_usuario_admin(self):
        usuario = self.novo_user_entry.get().strip()
        senha = self.novo_senha_entry.get().strip()
        cidade = self.novo_cidade_combo.get()
        tipo = self.novo_tipo_var.get()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha usuário e senha.")
            return
        if usuario in self.usuarios:
            messagebox.showerror("Erro", "Usuário já existe.")
            return

        self.usuarios[usuario] = {
            'senha_hash': hashlib.sha256(senha.encode()).hexdigest(),
            'tipo': tipo,
            'cidade': cidade if cidade else None
        }
        self.salvar_tudo()
        self.atualizar_lista_usuarios()
        messagebox.showinfo("Sucesso", "Usuário cadastrado.")
        self.novo_user_entry.delete(0, 'end')
        self.novo_senha_entry.delete(0, 'end')
        self.novo_cidade_combo.set('')

    def excluir_usuario_admin(self):
        selecionado = self.tree_usuarios.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um usuário.")
            return
        usuario = self.tree_usuarios.item(selecionado[0])['values'][0]
        if usuario == 'admin':
            messagebox.showerror("Erro", "Não é possível excluir o admin padrão.")
            return
        if messagebox.askyesno("Confirmar", f"Deseja excluir o usuário '{usuario}'?"):
            del self.usuarios[usuario]
            self.salvar_tudo()
            self.atualizar_lista_usuarios()
            messagebox.showinfo("Sucesso", "Usuário removido.")

    def atualizar_lista_usuarios(self):
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
        for user, dados in self.usuarios.items():
            cidade = dados.get('cidade', '')
            self.tree_usuarios.insert('', 'end', values=(user, dados['tipo'], cidade))

    # ==================== CRUD COMPROMISSOS ====================
    def abrir_calendario_admin(self):
        cidade = self.cidade_var.get()
        if cidade not in self.cidades_sc:
            messagebox.showwarning("Aviso", "Selecione uma cidade válida.")
            return
        comps = self.agenda.get(cidade, [])
        CalendarioWindow(self.root, cidade, comps, callback_global=self.atualizar_tabela_admin)

    def adicionar_compromisso(self):
        cidade = self.cidade_var.get()
        data_str = self.entry_data.get().strip()
        hora = self.entry_hora.get().strip()
        desc = self.entry_desc.get().strip()

        if cidade not in self.cidades_sc:
            messagebox.showerror("Erro", "Selecione uma cidade válida.")
            return
        if not data_str or not hora or not desc:
            messagebox.showwarning("Aviso", "Preencha todos os campos.")
            return
        try:
            data_dt = datetime.strptime(data_str, "%d/%m/%Y")
            data_iso = data_dt.strftime("%Y-%m-%d")
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            messagebox.showerror("Erro", "Formato inválido. Use DD/MM/AAAA e HH:MM.")
            return

        # Verificar se a data não é passado
        if data_dt.date() < datetime.now().date():
            messagebox.showerror("Erro", "Não é possível agendar no passado.")
            return

        # Verificar conflito de horário
        for comp in self.agenda.get(cidade, []):
            if comp['data_iso'] == data_iso and comp['hora'] == hora:
                messagebox.showerror("Erro", "Já existe um compromisso nesse horário.")
                return

        compromisso = {"data_iso": data_iso, "hora": hora, "descricao": desc, "checkin": False}
        self.agenda.setdefault(cidade, []).append(compromisso)
        self.agenda[cidade].sort(key=lambda x: (x['data_iso'], x['hora']))
        self.salvar_tudo()
        self.atualizar_tabela_admin()
        limpar_campos()
        messagebox.showinfo("Sucesso", "Compromisso adicionado!")

        def limpar_campos():
            self.entry_data.delete(0, 'end')
            self.entry_hora.delete(0, 'end')
            self.entry_desc.delete(0, 'end')

    def editar_compromisso(self):
        cidade = self.cidade_var.get()
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso.")
            return
        item = self.tree.item(selecionado[0])['values']
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            return

        # Janela de edição
        janela_editar = tk.Toplevel(self.root)
        janela_editar.title("Editar Compromisso")
        janela_editar.geometry("400x250")
        janela_editar.grab_set()

        frame = ttk.Frame(janela_editar, padding=15)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Data (DD/MM/AAAA):").grid(row=0, column=0, sticky='w')
        entry_data_edit = ttk.Entry(frame, width=15)
        entry_data_edit.grid(row=0, column=1, pady=5)
        entry_data_edit.insert(0, data_exibida)

        ttk.Label(frame, text="Hora (HH:MM):").grid(row=1, column=0, sticky='w')
        entry_hora_edit = ttk.Entry(frame, width=15)
        entry_hora_edit.grid(row=1, column=1, pady=5)
        entry_hora_edit.insert(0, hora)

        ttk.Label(frame, text="Descrição:").grid(row=2, column=0, sticky='w')
        entry_desc_edit = ttk.Entry(frame, width=30)
        entry_desc_edit.grid(row=2, column=1, pady=5)
        entry_desc_edit.insert(0, desc)

        def salvar_edicao():
            nova_data_str = entry_data_edit.get().strip()
            nova_hora = entry_hora_edit.get().strip()
            nova_desc = entry_desc_edit.get().strip()
            try:
                nova_data_dt = datetime.strptime(nova_data_str, "%d/%m/%Y")
                nova_data_iso = nova_data_dt.strftime("%Y-%m-%d")
                datetime.strptime(nova_hora, "%H:%M")
            except ValueError:
                messagebox.showerror("Erro", "Formato inválido.", parent=janela_editar)
                return

            # Atualizar na lista
            for comp in self.agenda.get(cidade, []):
                if comp['data_iso'] == data_iso and comp['hora'] == hora and comp['descricao'] == desc:
                    comp['data_iso'] = nova_data_iso
                    comp['hora'] = nova_hora
                    comp['descricao'] = nova_desc
                    break
            self.salvar_tudo()
            self.atualizar_tabela_admin()
            janela_editar.destroy()
            messagebox.showinfo("Sucesso", "Compromisso atualizado.")

        ttk.Button(frame, text="Salvar", command=salvar_edicao).grid(row=3, column=0, columnspan=2, pady=20)

    def remover_compromisso(self):
        cidade = self.cidade_var.get()
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso.")
            return
        item = self.tree.item(selecionado[0])['values']
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        if not messagebox.askyesno("Confirmar", "Remover este compromisso?"):
            return
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            return
        if cidade in self.agenda:
            self.agenda[cidade] = [c for c in self.agenda[cidade]
                                   if not (c['data_iso']==data_iso and c['hora']==hora and c['descricao']==desc)]
            if not self.agenda[cidade]:
                del self.agenda[cidade]
            self.salvar_tudo()
            self.atualizar_tabela_admin()

    def checkin_admin(self):
        cidade = self.cidade_var.get()
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso.")
            return
        item = self.tree.item(selecionado[0])['values']
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        if status == 'Confirmado':
            messagebox.showinfo("Aviso", "Check-in já realizado.")
            return
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            return
        if cidade in self.agenda:
            for comp in self.agenda[cidade]:
                if comp['data_iso']==data_iso and comp['hora']==hora and comp['descricao']==desc:
                    comp['checkin'] = True
                    break
            self.salvar_tudo()
            self.atualizar_tabela_admin()

    def atualizar_tabela_admin(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        cidade = self.cidade_var.get()
        if cidade in self.agenda:
            for comp in sorted(self.agenda[cidade], key=lambda x: (x['data_iso'], x['hora'])):
                data_fmt = datetime.strptime(comp['data_iso'], "%Y-%m-%d").strftime("%d/%m/%Y")
                status = "Confirmado" if comp.get('checkin', False) else "Pendente"
                self.tree.insert("", "end", values=(data_fmt, comp['hora'], comp['descricao'], status))

    # ==================== PAINEL USUÁRIO ====================
    def painel_usuario(self, cidade_fixa=None):
        self.limpar_tela()
        self.root.geometry("750x500")
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill='both', expand=True)

        if cidade_fixa:
            ttk.Label(frame, text=f"Agenda de {cidade_fixa}", font=('Segoe UI', 14, 'bold')).pack(pady=5)
            self.cidade_usuario_var = tk.StringVar(value=cidade_fixa)
        else:
            ttk.Label(frame, text="Consulta de Agenda por Cidade", font=('Segoe UI', 14, 'bold')).pack(pady=5)
            ttk.Label(frame, text="Selecione a cidade:").pack(anchor='w')
            self.cidade_usuario_var = tk.StringVar()
            combo = AutocompleteCombobox(frame, self.cidades_sc, textvariable=self.cidade_usuario_var, width=40)
            combo.pack(fill='x', pady=5)
            combo.set("Escolha uma cidade")

        botoes_frame = ttk.Frame(frame)
        botoes_frame.pack(pady=10)
        ttk.Button(botoes_frame, text="📋 Tabela", command=self.mostrar_agenda_usuario).pack(side='left', padx=5)
        ttk.Button(botoes_frame, text="📅 Calendário", command=self.abrir_calendario_usuario).pack(side='left', padx=5)
        ttk.Button(botoes_frame, text="✔ Check-in", command=self.checkin_usuario).pack(side='left', padx=5)

        colunas = ('Data', 'Hora', 'Compromisso', 'Status')
        self.tree_usuario = ttk.Treeview(frame, columns=colunas, show='headings', height=12)
        for col in colunas:
            self.tree_usuario.heading(col, text=col)
            self.tree_usuario.column(col, width=120 if col != 'Compromisso' else 300)
        self.tree_usuario.pack(fill='both', expand=True, pady=5)

        ttk.Button(frame, text="Logout", command=self.criar_tela_login).pack(pady=10)

        if cidade_fixa:
            self.mostrar_agenda_usuario()

    def abrir_calendario_usuario(self):
        cidade = self.cidade_usuario_var.get()
        if cidade not in self.cidades_sc:
            messagebox.showwarning("Aviso", "Selecione uma cidade válida.")
            return
        comps = self.agenda.get(cidade, [])
        CalendarioWindow(self.root, cidade, comps, callback_global=self.mostrar_agenda_usuario)

    def mostrar_agenda_usuario(self):
        cidade = self.cidade_usuario_var.get()
        for i in self.tree_usuario.get_children():
            self.tree_usuario.delete(i)
        if cidade not in self.cidades_sc:
            messagebox.showwarning("Aviso", "Selecione uma cidade.")
            return
        if cidade not in self.agenda or not self.agenda[cidade]:
            messagebox.showinfo("Informação", f"Nenhum compromisso em {cidade}.")
            return
        for comp in sorted(self.agenda[cidade], key=lambda x: (x['data_iso'], x['hora'])):
            data_fmt = datetime.strptime(comp['data_iso'], "%Y-%m-%d").strftime("%d/%m/%Y")
            status = "Confirmado" if comp.get('checkin', False) else "Pendente"
            self.tree_usuario.insert("", "end", values=(data_fmt, comp['hora'], comp['descricao'], status))

    def checkin_usuario(self):
        cidade = self.cidade_usuario_var.get()
        selecionado = self.tree_usuario.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso.")
            return
        item = self.tree_usuario.item(selecionado[0])['values']
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        if status == 'Confirmado':
            messagebox.showinfo("Aviso", "Check-in já realizado.")
            return
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            return
        if cidade in self.agenda:
            for comp in self.agenda[cidade]:
                if comp['data_iso']==data_iso and comp['hora']==hora and comp['descricao']==desc:
                    comp['checkin'] = True
                    break
            self.salvar_tudo()
            self.mostrar_agenda_usuario()
            messagebox.showinfo("Sucesso", "Check-in realizado!")

# ==================== EXECUÇÃO ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaAgenda(root)
    root.mainloop()