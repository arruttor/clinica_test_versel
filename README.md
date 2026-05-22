# 🏥 Clínica Edu UNA

![Banner](./docs/images/banner.png)

## 📋 Sobre o Projeto

O **Clínica Edu UNA** é um sistema de gestão integrado desenvolvido especificamente para atender às necessidades de uma **Clínica Escola Universitária**. O sistema une a gestão de atendimentos de saúde (Odontologia, Psicologia, Fisioterapia e Enfermagem) com o acompanhamento pedagógico dos alunos e a gestão de recursos físicos e insumos.

O objetivo principal é digitalizar o fluxo de atendimento, desde a triagem na lista de espera até a evolução clínica supervisionada, garantindo conformidade com as práticas acadêmicas e eficiência administrativa.

---

## ✨ Funcionalidades Principais

### 🩺 Módulo Clínico
- **Prontuário Eletrônico (PEP):** Registro completo de atendimentos e evoluções.
- **Anamnese Personalizada:** Formulários de histórico médico, alergias e queixas principais adaptados para cada especialidade.
- **Gestão de Pacientes:** Cadastro completo com CPF, contatos e observações.
- **Upload de Documentos:** Anexo de exames, radiografias e termos de consentimento diretamente na ficha do paciente.

### 🎓 Módulo Acadêmico & Supervisão
- **Supervisão Docente:** Fluxo de aprovação de evoluções, onde professores avaliam e dão notas ao desempenho dos alunos.
- **Duplas de Odontologia:** Gestão específica para o curso de Odontologia, permitindo o trabalho em duplas de acadêmicos.
- **Log de Auditoria:** Rastreabilidade total de alterações em avaliações e prontuários.
- **Produção Acadêmica:** Relatórios de desempenho por aluno e por clínica.

### 📅 Gestão de Agenda & Recursos
- **Agenda Interativa:** Visualização e controle de marcações por clínica e profissional.
- **Controle de Boxes/Salas:** Gestão física de consultórios, cadeiras e macas para evitar overbooking.
- **Lista de Espera Inteligente:** Triagem e fila de espera organizada por especialidade e status.

### 📦 Almoxarifado (Estoque)
- **Catálogo de Insumos:** Controle de materiais clínicos (anestésicos, luvas, resinas, etc.).
- **Movimentações:** Registro rigoroso de entradas e saídas.
- **Alertas de Estoque Baixo:** Sistema de aviso automático para reposição de materiais críticos.

---

## 🚀 Tecnologias Utilizadas

- **Backend:** [Django 5.1+](https://www.djangoproject.com/)
- **Linguagem:** [Python 3.10+](https://www.python.org/)
- **Banco de Dados:** SQLite (Desenvolvimento) / PostgreSQL (Produção sugerido)
- **Frontend:** Django Templates com Vanilla CSS/JS
- **Internacionalização:** Suporte nativo a `pt-br`

---

## ⚙️ Instalação e Execução

### Pré-requisitos
- Python 3.10 ou superior
- Pip (gerenciador de pacotes)

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/usuario/clinica_edu_una.git
   cd clinica_edu_una
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows:
   .\venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install django
   # Ou se houver um requirements.txt:
   # pip install -r requirements.txt
   ```

4. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

5. **(Opcional) Popule o banco com dados iniciais:**
   ```bash
   python populate_clinica.py
   ```

6. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```
   Acesse em: `http://127.0.0.1:8000`

---

## 📂 Estrutura do Projeto

```text
clinica_edu_una/
├── clinica_core/       # App principal (Models, Views, Forms)
├── clinica_edu/        # Configurações do projeto Django
├── media/              # Arquivos de mídia (uploads de pacientes)
├── templates/          # Templates HTML globais
├── static/             # Arquivos estáticos (CSS, JS, Imagens)
├── docs/               # Documentação e ativos do README
└── manage.py           # Script de gerenciamento Django
```

---

## 📊 Dashboards e Relatórios
O sistema conta com um painel administrativo robusto que permite visualizar:
- Atendimentos por período.
- Taxa de absenteísmo (faltas).
- Ocupação de recursos físicos.
- Consumo de materiais por clínica.

---

## 🤝 Contribuição
1. Faça um Fork do projeto.
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFeature`).
3. Comite suas mudanças (`git commit -m 'Adicionando uma nova funcionalidade'`).
4. Faça o Push para a branch (`git push origin feature/NovaFeature`).
5. Abra um Pull Request.

---

## 📄 Licença
Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---
Desenvolvido para a **UNA - Centro Universitário**. 🎓🏥


Desenvolvido por:
* Giuliano Richards Ribeiro
* Vinícius Borges
