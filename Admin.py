import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import os

class DetalhesDiaWindow(tk.Toplevel):
    """Janela pop-up com os compromissos de um dia específico"""
    def __init__(self, parent, data_iso, compromissos_do_dia, callback_atualizar):
        super().__init__(parent)
        self.data_iso = data_iso
        self.compromissos = compromissos_do_dia
        self.callback_atualizar = callback_atualizar
        self.title(f"Compromissos - {self._formatar_data(data_iso)}")
        self.geometry("450x400")
        self.resizable(False, False)
        self.grab_set()

        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=f"Compromissos em {self._formatar_data(data_iso)}",
                 font=("Arial", 12, "bold")).pack(pady=(0,10))

        if not self.compromissos:
            tk.Label(frame, text="Nenhum compromisso neste dia.", fg="gray").pack()
            tk.Button(frame, text="Fechar", command=self.destroy).pack(pady=20)
            return

        canvas = tk.Canvas(frame, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.criar_lista_compromissos()

        tk.Button(frame, text="Fechar", command=self.destroy).pack(pady=10)

    def _formatar_data(self, data_iso):
        try:
            dt = datetime.strptime(data_iso, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except:
            return data_iso

    def criar_lista_compromissos(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for comp in sorted(self.compromissos, key=lambda x: x["hora"]):
            frame_comp = tk.Frame(self.scroll_frame, relief="groove", borderwidth=1, pady=3, padx=5)
            frame_comp.pack(fill="x", pady=2)

            info = f"{comp['hora']} - {comp['descricao']}"
            status = "✅ Confirmado" if comp.get("checkin", False) else "⏳ Pendente"
            cor_status = "green" if comp.get("checkin", False) else "orange"

            tk.Label(frame_comp, text=info, font=("Arial", 10)).pack(side="left", padx=5)
            tk.Label(frame_comp, text=status, fg=cor_status, font=("Arial", 9, "bold")).pack(side="left", padx=10)

            if not comp.get("checkin", False):
                btn = tk.Button(frame_comp, text="Fazer Check-in", bg="lightgreen",
                                command=lambda c=comp: self.realizar_checkin(c))
                btn.pack(side="right", padx=5)

    def realizar_checkin(self, compromisso):
        compromisso["checkin"] = True
        self.criar_lista_compromissos()
        if self.callback_atualizar:
            self.callback_atualizar()


class CalendarioWindow(tk.Toplevel):
    """Janela de calendário mensal com compromissos integrados nos dias"""
    def __init__(self, parent, cidade, compromissos):
        super().__init__(parent)
        self.title(f"Agenda - {cidade}")
        self.geometry("550x500")
        self.resizable(False, False)
        self.cidade = cidade
        self.compromissos = compromissos
        self.hoje = datetime.now()
        self.ano_atual = self.hoje.year
        self.mes_atual = self.hoje.month

        header = tk.Frame(self)
        header.pack(pady=10)
        self.btn_anterior = tk.Button(header, text="◀", command=self.mes_anterior)
        self.btn_anterior.pack(side="left", padx=5)
        self.lbl_mes = tk.Label(header, text="", font=("Arial", 14, "bold"), width=20)
        self.lbl_mes.pack(side="left", padx=5)
        self.btn_proximo = tk.Button(header, text="▶", command=self.proximo_mes)
        self.btn_proximo.pack(side="left", padx=5)

        self.frame_calendario = tk.Frame(self)
        self.frame_calendario.pack(pady=10)

        self.atualizar_calendario()

    def obter_compromissos_do_dia(self, data_iso):
        return [c for c in self.compromissos if c["data_iso"] == data_iso]

    def atualizar_calendario(self):
        for widget in self.frame_calendario.winfo_children():
            widget.destroy()

        self.lbl_mes.config(text=f"{calendar.month_name[self.mes_atual]} de {self.ano_atual}")

        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for i, dia in enumerate(dias_semana):
            lbl = tk.Label(self.frame_calendario, text=dia, font=("Arial", 9, "bold"), width=10, relief="ridge")
            lbl.grid(row=0, column=i, padx=1, pady=1)

        cal = calendar.monthcalendar(self.ano_atual, self.mes_atual)
        for r, semana in enumerate(cal):
            for c, dia in enumerate(semana):
                if dia != 0:
                    data_iso = f"{self.ano_atual:04d}-{self.mes_atual:02d}-{dia:02d}"
                    comps_dia = self.obter_compromissos_do_dia(data_iso)

                    frame_dia = tk.Frame(self.frame_calendario, relief="ridge", borderwidth=1, width=80, height=80)
                    frame_dia.grid(row=r+1, column=c, padx=1, pady=1, sticky="nsew")
                    frame_dia.pack_propagate(False)

                    cor_num = "red" if (self.ano_atual, self.mes_atual, dia) == (self.hoje.year, self.hoje.month, self.hoje.day) else "black"
                    lbl_num = tk.Label(frame_dia, text=str(dia), font=("Arial", 9, "bold"), fg=cor_num)
                    lbl_num.pack(anchor="nw", padx=2, pady=2)

                    if comps_dia:
                        comps_ordenados = sorted(comps_dia, key=lambda x: x["hora"])
                        max_exibir = 3
                        for i, comp in enumerate(comps_ordenados[:max_exibir]):
                            hora = comp["hora"]
                            checkin = comp.get("checkin", False)
                            cor_texto = "green" if checkin else "black"
                            texto = f"{hora}"
                            if i == max_exibir-1 and len(comps_ordenados) > max_exibir:
                                texto += " ..."
                            lbl_comp = tk.Label(frame_dia, text=texto, font=("Arial", 7), fg=cor_texto, anchor="w")
                            lbl_comp.pack(anchor="w", padx=2)

                    frame_dia.bind("<Button-1>", lambda e, d=data_iso: self._abrir_popup(d))
                    lbl_num.bind("<Button-1>", lambda e, d=data_iso: self._abrir_popup(d))
                    for child in frame_dia.winfo_children():
                        child.bind("<Button-1>", lambda e, d=data_iso: self._abrir_popup(d))
                else:
                    lbl_vazio = tk.Label(self.frame_calendario, text="", width=10, height=4, relief="ridge", bg="lightgray")
                    lbl_vazio.grid(row=r+1, column=c, padx=1, pady=1)

    def _abrir_popup(self, data_iso):
        comps = self.obter_compromissos_do_dia(data_iso)
        DetalhesDiaWindow(self, data_iso, comps, callback_atualizar=self.atualizar_calendario)

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


class SistemaAgenda:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Agenda - SC")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.credenciais_fixas = {
            "admin": {"senha": "admin123", "tipo": "ADM"},
            "usuario": {"senha": "user123", "tipo": "Usuário"}  # usuário genérico
        }

        # Usuários fixos por cidade
        self.usuarios_cidades = {
            "portouniao": {"senha": "1234", "cidade": "Porto União"},
            "florianopolis": {"senha": "1234", "cidade": "Florianópolis"},
            "joinville": {"senha": "1234", "cidade": "Joinville"},
            "blumenau": {"senha": "1234", "cidade": "Blumenau"},
            "chapeco": {"senha": "1234", "cidade": "Chapecó"}
        }

        self.agenda = {}
        self.arquivo_usuarios = "usuarios.txt"
        self.usuarios_txt = self.carregar_usuarios_txt()

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
        hoje = datetime.now().strftime("%Y-%m-%d")
        amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        depois = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        exemplos = {
            "Porto União": [
                {"data_iso": hoje, "hora": "09:00", "descricao": "Reunião com fornecedores", "checkin": False},
                {"data_iso": hoje, "hora": "14:00", "descricao": "Visita técnica à fábrica", "checkin": False},
                {"data_iso": amanha, "hora": "10:00", "descricao": "Treinamento equipe", "checkin": False},
                {"data_iso": depois, "hora": "08:30", "descricao": "Entrega de relatórios", "checkin": False}
            ],
            "Florianópolis": [
                {"data_iso": hoje, "hora": "11:00", "descricao": "Reunião diretoria", "checkin": False},
                {"data_iso": amanha, "hora": "15:00", "descricao": "Palestra inovação", "checkin": False}
            ],
            "Joinville": [
                {"data_iso": hoje, "hora": "08:00", "descricao": "Feira industrial", "checkin": False},
                {"data_iso": amanha, "hora": "09:30", "descricao": "Workshop software", "checkin": False}
            ],
            "Blumenau": [
                {"data_iso": hoje, "hora": "13:00", "descricao": "Almoço executivo", "checkin": False},
                {"data_iso": depois, "hora": "16:00", "descricao": "Apresentação de resultados", "checkin": False}
            ],
            "Chapecó": [
                {"data_iso": amanha, "hora": "07:30", "descricao": "Visita ao campo", "checkin": False},
                {"data_iso": depois, "hora": "09:00", "descricao": "Negociação safra", "checkin": False}
            ]
        }
        for cidade, comps in exemplos.items():
            self.agenda[cidade] = comps

    # ---------- MANIPULAÇÃO DO ARQUIVO TXT ----------
    def carregar_usuarios_txt(self):
        usuarios = {}
        if os.path.exists(self.arquivo_usuarios):
            with open(self.arquivo_usuarios, "r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha and "," in linha:
                        partes = linha.split(",", 1)
                        if len(partes) == 2:
                            user, senha = partes[0].strip(), partes[1].strip()
                            if user and senha:
                                usuarios[user] = senha
        return usuarios

    def salvar_usuario_txt(self, usuario, senha):
        with open(self.arquivo_usuarios, "a", encoding="utf-8") as f:
            f.write(f"{usuario},{senha}\n")

    def limpar_tela(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ==================== LOGIN ====================
    def criar_tela_login(self):
        self.limpar_tela()
        self.root.geometry("500x400")
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Acesso ao Sistema", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,15))

        tk.Label(frame, text="Tipo de acesso:").grid(row=1, column=0, sticky="w", pady=5)
        self.tipo_var = tk.StringVar(value="Usuário")
        tk.Radiobutton(frame, text="Administrador", variable=self.tipo_var, value="ADM").grid(row=1, column=1, sticky="w")
        tk.Radiobutton(frame, text="Usuário", variable=self.tipo_var, value="Usuário").grid(row=2, column=1, sticky="w")

        tk.Label(frame, text="Usuário:").grid(row=3, column=0, sticky="w", pady=(10,0))
        self.entry_usuario = tk.Entry(frame, width=25)
        self.entry_usuario.grid(row=3, column=1, pady=(10,0))

        tk.Label(frame, text="Senha:").grid(row=4, column=0, sticky="w", pady=5)
        self.entry_senha = tk.Entry(frame, width=25, show="*")
        self.entry_senha.grid(row=4, column=1, pady=5)

        botoes_frame = tk.Frame(frame)
        botoes_frame.grid(row=5, column=0, columnspan=2, pady=20)
        tk.Button(botoes_frame, text="Entrar", command=self.verificar_login, width=12).pack(side="left", padx=5)
        tk.Button(botoes_frame, text="Cadastrar-se", command=self.abrir_tela_cadastro, width=12).pack(side="left", padx=5)

    def verificar_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()
        tipo_selecionado = self.tipo_var.get()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha todos os campos.")
            return

        # 1. Credenciais fixas (admin e usuario genérico)
        if usuario in self.credenciais_fixas:
            if self.credenciais_fixas[usuario]["senha"] == senha:
                tipo_real = self.credenciais_fixas[usuario]["tipo"]
                if tipo_selecionado != tipo_real:
                    messagebox.showerror("Erro", f"Usuário '{usuario}' não é do tipo {tipo_selecionado}.")
                    return
                messagebox.showinfo("Sucesso", f"Bem-vindo(a), {usuario}!")
                if tipo_real == "ADM":
                    self.painel_admin()
                else:
                    self.painel_usuario()  # usuário genérico
                return
            else:
                messagebox.showerror("Erro", "Usuário ou senha inválidos.")
                return

        # 2. Usuários fixos por cidade
        if usuario in self.usuarios_cidades:
            if self.usuarios_cidades[usuario]["senha"] == senha:
                if tipo_selecionado != "Usuário":
                    messagebox.showerror("Erro", "Este usuário não é administrador.")
                    return
                cidade = self.usuarios_cidades[usuario]["cidade"]
                messagebox.showinfo("Sucesso", f"Bem-vindo(a), {usuario}!\nCidade: {cidade}")
                self.painel_usuario(cidade_fixa=cidade)
                return
            else:
                messagebox.showerror("Erro", "Usuário ou senha inválidos.")
                return

        # 3. Usuários cadastrados via TXT
        if usuario in self.usuarios_txt and self.usuarios_txt[usuario] == senha:
            if tipo_selecionado != "Usuário":
                messagebox.showerror("Erro", f"O usuário '{usuario}' não é Administrador.")
                return
            messagebox.showinfo("Sucesso", f"Bem-vindo(a), {usuario}!")
            self.painel_usuario()
            return

        messagebox.showerror("Erro", "Usuário ou senha inválidos.")

    # ==================== CADASTRO ====================
    def abrir_tela_cadastro(self):
        janela_cadastro = tk.Toplevel(self.root)
        janela_cadastro.title("Cadastrar novo usuário")
        janela_cadastro.geometry("350x250")
        janela_cadastro.resizable(False, False)
        janela_cadastro.grab_set()

        frame = tk.Frame(janela_cadastro, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Criar conta de Usuário", font=("Arial", 12, "bold")).pack(pady=(0,10))
        tk.Label(frame, text="Nome de usuário:").pack(anchor="w")
        entry_novo_usuario = tk.Entry(frame, width=30)
        entry_novo_usuario.pack(pady=2)
        tk.Label(frame, text="Senha:").pack(anchor="w")
        entry_nova_senha = tk.Entry(frame, width=30, show="*")
        entry_nova_senha.pack(pady=2)
        tk.Label(frame, text="Confirmar senha:").pack(anchor="w")
        entry_confirma_senha = tk.Entry(frame, width=30, show="*")
        entry_confirma_senha.pack(pady=2)

        def realizar_cadastro():
            usuario = entry_novo_usuario.get().strip()
            senha = entry_nova_senha.get().strip()
            confirma = entry_confirma_senha.get().strip()
            if not usuario or not senha or not confirma:
                messagebox.showwarning("Aviso", "Preencha todos os campos.", parent=janela_cadastro)
                return
            if usuario in self.credenciais_fixas or usuario in self.usuarios_cidades or usuario in self.usuarios_txt:
                messagebox.showerror("Erro", "Este nome de usuário já está em uso.", parent=janela_cadastro)
                return
            if senha != confirma:
                messagebox.showerror("Erro", "As senhas não coincidem.", parent=janela_cadastro)
                return
            self.salvar_usuario_txt(usuario, senha)
            self.usuarios_txt[usuario] = senha
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!\nAgora você pode fazer login.", parent=janela_cadastro)
            janela_cadastro.destroy()

        tk.Button(frame, text="Cadastrar", command=realizar_cadastro, width=20).pack(pady=15)

    # ==================== PAINEL ADMIN ====================
    def painel_admin(self):
        self.limpar_tela()
        self.root.geometry("700x550")
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Painel do Administrador", font=("Arial", 14, "bold")).pack(pady=5)

        tk.Label(frame, text="Cidade:").pack(anchor="w")
        self.cidade_var = tk.StringVar()
        self.combo_cidade = ttk.Combobox(frame, textvariable=self.cidade_var, values=self.cidades_sc, state="readonly", width=40)
        self.combo_cidade.pack(fill="x", pady=2)
        self.combo_cidade.set("Selecione uma cidade")

        campos = tk.Frame(frame)
        campos.pack(pady=5)
        tk.Label(campos, text="Data (DD/MM/AAAA):").grid(row=0, column=0, sticky="w")
        self.entry_data = tk.Entry(campos, width=12)
        self.entry_data.grid(row=0, column=1, padx=5)
        tk.Label(campos, text="Hora (HH:MM):").grid(row=0, column=2, sticky="w")
        self.entry_hora = tk.Entry(campos, width=8)
        self.entry_hora.grid(row=0, column=3, padx=5)

        tk.Label(frame, text="Descrição:").pack(anchor="w")
        self.entry_desc = tk.Entry(frame, width=50)
        self.entry_desc.pack(fill="x", pady=2)

        botoes = tk.Frame(frame)
        botoes.pack(pady=10)
        tk.Button(botoes, text="Adicionar", command=self.adicionar_compromisso).pack(side="left", padx=5)
        tk.Button(botoes, text="Remover", command=self.remover_compromisso).pack(side="left", padx=5)
        tk.Button(botoes, text="Check-in", command=self.checkin_admin).pack(side="left", padx=5)
        tk.Button(botoes, text="Ver Calendário", command=self.abrir_calendario_admin).pack(side="left", padx=5)

        tk.Label(frame, text="Compromissos da cidade:").pack(anchor="w", pady=(10,0))
        self.tree = ttk.Treeview(frame, columns=("Data", "Hora", "Descrição", "Status"), show="headings", height=8)
        self.tree.heading("Data", text="Data")
        self.tree.heading("Hora", text="Hora")
        self.tree.heading("Descrição", text="Descrição")
        self.tree.heading("Status", text="Status")
        self.tree.column("Data", width=100)
        self.tree.column("Hora", width=80)
        self.tree.column("Descrição", width=250)
        self.tree.column("Status", width=100)
        self.tree.pack(fill="both", expand=True, pady=5)

        self.combo_cidade.bind("<<ComboboxSelected>>", lambda e: self.atualizar_tabela_admin())
        tk.Button(frame, text="Logout", command=self.criar_tela_login, bg="lightcoral").pack(pady=10)

    def abrir_calendario_admin(self):
        cidade = self.cidade_var.get()
        if cidade not in self.cidades_sc:
            messagebox.showwarning("Aviso", "Selecione uma cidade válida.")
            return
        comps = self.agenda.get(cidade, [])
        CalendarioWindow(self.root, cidade, comps)

    def adicionar_compromisso(self):
        cidade = self.cidade_var.get()
        data_str = self.entry_data.get().strip()
        hora = self.entry_hora.get().strip()
        desc = self.entry_desc.get().strip()

        if cidade not in self.cidades_sc:
            messagebox.showerror("Erro", "Selecione uma cidade válida.")
            return
        if not data_str or not hora or not desc:
            messagebox.showwarning("Aviso", "Preencha data, hora e descrição.")
            return
        try:
            data_dt = datetime.strptime(data_str, "%d/%m/%Y")
            data_iso = data_dt.strftime("%Y-%m-%d")
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            messagebox.showerror("Erro", "Formato inválido. Use DD/MM/AAAA para data e HH:MM para hora.")
            return

        compromisso = {"data_iso": data_iso, "hora": hora, "descricao": desc, "checkin": False}
        self.agenda.setdefault(cidade, []).append(compromisso)
        self.agenda[cidade].sort(key=lambda x: (x["data_iso"], x["hora"]))

        self.entry_data.delete(0, tk.END)
        self.entry_hora.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.atualizar_tabela_admin()
        messagebox.showinfo("Sucesso", "Compromisso adicionado!")

    def remover_compromisso(self):
        cidade = self.cidade_var.get()
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso na tabela.")
            return
        item = self.tree.item(selecionado[0])["values"]
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return
        if cidade in self.agenda:
            self.agenda[cidade] = [c for c in self.agenda[cidade] 
                                   if not (c["data_iso"]==data_iso and c["hora"]==hora and c["descricao"]==desc)]
            if not self.agenda[cidade]:
                del self.agenda[cidade]
            self.atualizar_tabela_admin()

    def checkin_admin(self):
        cidade = self.cidade_var.get()
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso na tabela.")
            return
        item = self.tree.item(selecionado[0])["values"]
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        if status == "Confirmado":
            messagebox.showinfo("Aviso", "Check-in já realizado.")
            return
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return
        if cidade in self.agenda:
            for comp in self.agenda[cidade]:
                if comp["data_iso"] == data_iso and comp["hora"] == hora and comp["descricao"] == desc:
                    comp["checkin"] = True
                    break
            self.atualizar_tabela_admin()

    def atualizar_tabela_admin(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        cidade = self.cidade_var.get()
        if cidade in self.agenda:
            for comp in self.agenda[cidade]:
                data_formatada = datetime.strptime(comp["data_iso"], "%Y-%m-%d").strftime("%d/%m/%Y")
                status = "Confirmado" if comp.get("checkin", False) else "Pendente"
                self.tree.insert("", "end", values=(data_formatada, comp["hora"], comp["descricao"], status))

    # ==================== PAINEL USUÁRIO (AGORA ACEITA CIDADE FIXA) ====================
    def painel_usuario(self, cidade_fixa=None):
        self.limpar_tela()
        self.root.geometry("700x450")
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        if cidade_fixa:
            tk.Label(frame, text=f"Agenda de {cidade_fixa}", font=("Arial", 14, "bold")).pack(pady=5)
            self.cidade_usuario_var = tk.StringVar(value=cidade_fixa)
            # Não exibe o combobox
        else:
            tk.Label(frame, text="Consulta de Agenda por Cidade", font=("Arial", 14, "bold")).pack(pady=5)
            tk.Label(frame, text="Selecione a cidade:").pack(anchor="w")
            self.cidade_usuario_var = tk.StringVar()
            combo = ttk.Combobox(frame, textvariable=self.cidade_usuario_var, values=self.cidades_sc, state="readonly", width=40)
            combo.pack(fill="x", pady=5)
            combo.set("Escolha uma cidade")

        botoes_frame = tk.Frame(frame)
        botoes_frame.pack(pady=5)
        tk.Button(botoes_frame, text="Visualizar Agenda (Tabela)", command=self.mostrar_agenda_usuario).pack(side="left", padx=5)
        tk.Button(botoes_frame, text="Visualizar Calendário", command=self.abrir_calendario_usuario).pack(side="left", padx=5)
        tk.Button(botoes_frame, text="Check-in (Selecionado)", command=self.checkin_usuario).pack(side="left", padx=5)

        self.tree_usuario = ttk.Treeview(frame, columns=("Data", "Hora", "Compromisso", "Status"), show="headings", height=10)
        self.tree_usuario.heading("Data", text="Data")
        self.tree_usuario.heading("Hora", text="Hora")
        self.tree_usuario.heading("Compromisso", text="Compromisso")
        self.tree_usuario.heading("Status", text="Status")
        self.tree_usuario.column("Data", width=100)
        self.tree_usuario.column("Hora", width=80)
        self.tree_usuario.column("Compromisso", width=300)
        self.tree_usuario.column("Status", width=100)
        self.tree_usuario.pack(fill="both", expand=True, pady=10)

        tk.Button(frame, text="Logout", command=self.criar_tela_login, bg="lightcoral").pack(pady=10)

        # Se tem cidade fixa, já carrega a tabela automaticamente
        if cidade_fixa:
            self.mostrar_agenda_usuario()

    def abrir_calendario_usuario(self):
        cidade = self.cidade_usuario_var.get()
        if cidade not in self.cidades_sc:
            messagebox.showwarning("Aviso", "Selecione uma cidade válida.")
            return
        comps = self.agenda.get(cidade, [])
        CalendarioWindow(self.root, cidade, comps)

    def mostrar_agenda_usuario(self):
        cidade = self.cidade_usuario_var.get()
        for i in self.tree_usuario.get_children():
            self.tree_usuario.delete(i)
        if cidade not in self.cidades_sc:
            messagebox.showwarning("Aviso", "Selecione uma cidade válida.")
            return
        if cidade not in self.agenda or not self.agenda[cidade]:
            messagebox.showinfo("Informação", f"Nenhum compromisso encontrado para {cidade}.")
            return
        for comp in self.agenda[cidade]:
            data_formatada = datetime.strptime(comp["data_iso"], "%Y-%m-%d").strftime("%d/%m/%Y")
            status = "Confirmado" if comp.get("checkin", False) else "Pendente"
            self.tree_usuario.insert("", "end", values=(data_formatada, comp["hora"], comp["descricao"], status))

    def checkin_usuario(self):
        cidade = self.cidade_usuario_var.get()
        selecionado = self.tree_usuario.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um compromisso na tabela.")
            return
        item = self.tree_usuario.item(selecionado[0])["values"]
        data_exibida, hora, desc, status = item[0], item[1], item[2], item[3]
        if status == "Confirmado":
            messagebox.showinfo("Aviso", "Check-in já realizado.")
            return
        try:
            data_iso = datetime.strptime(data_exibida, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return
        if cidade in self.agenda:
            for comp in self.agenda[cidade]:
                if comp["data_iso"] == data_iso and comp["hora"] == hora and comp["descricao"] == desc:
                    comp["checkin"] = True
                    break
            self.mostrar_agenda_usuario()
            messagebox.showinfo("Sucesso", "Check-in realizado com sucesso!")

# Inicialização
if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaAgenda(root)
    root.mainloop()