# Módulo de Supervisão Docente (Aprovação)

A clínica universitária exige que os atendimentos dos alunos passem pela curadoria de um professor. Neste módulo será possível o cadastro de Alunos e Professores, e as evoluções clínicas só serão oficializadas pós-avaliação.

## Proposed Changes

### Modelagem do Banco (models.py)
#### [NEW] `Professor` 
- Vinculado (1:1) com a tabela `User` do Django para acessar o login.
- Terá vínculo com a `Clinica` em que atende.

#### [MODIFY] `Evolucao`
- Inclusão dos campos de fiscalização:
  - `status` (Aguardando / Aprovado)
  - `nota` (Decimal, 0 a 10)
  - `avaliador` (Ponteiro para o Professor)
  - `observacao_supervisor` (Caixa de texto para feedback ao aluno).
- Adicionaremos uma Permissão Especial de Django ("`can_approve_evolucao`") atrelada ao modelo. Assim, a interface gráfica saberá esconder ou liberar botões de curadoria usando apenas uma verificação de "Poderes" do usuário logado.

#### [MODIFY] `Academico`
- O modelo `Academico` (Tabela de aluno) já existia esquecido em `models.py` (criado nos primórdios do projeto). Adicionaremos a ligação (1:1) `usuario = OneToOneField(User)` também à ele para que o login que relata o PEP seja de um aluno válido no sistema.

### Formulários (forms.py)
- **[NEW] `AcademicoForm` e `ProfessorForm`**:  Formulários com o padrão visual dark/light do template. Eles envolverão criar o *Usuário Django* por trás dos panos (username + senha).
- **[NEW] `AprovacaoEvolucaoForm`**: Um campo restrito (só Nota, e Comentário) para a popup ou visão modal do Professor.

### Cadastros Básicos (CRUD de Pessoas)
#### [NEW] `urls.py` e `views.py`
Vamos habilitar telas para listar, cadastrar e deletar Professores e Acadêmicos (Alunos). Adicionaremos atalhos no menu "Cadastros" na barra lateral esquerda.

### Avaliação do PEP e Fluxo de Uso
1. **Atuação do Aluno**: O preenchimento da `Evolução` se mantém o mesmo pro aluno, mas na timeline da ficha, ficará com uma tarja "🟠 Status: Aguardando Supervisor" ao lado do atendimento que acabou de ser prestado.
2. **Caixa de Entrada Docente (`/aprovacoes/`)**: Construiremos uma aba nova no Menu principal (como a *Lista de Espera*) só para Professores: "**Área do Docente**". Nela, o professor enxerga todos os prontuários de sua clínica que precisam de aprovação (Status Aguardando).
3. **Oficializando Evolução**: Ao clicar em uma dessas avaliações pontuais, o professor envia uma nota (ex: 8.5) e clica em **"Aprovar"**, o que trava o PEP (ele fica verde e finalizado, visível à todos).

## User Review Required
Para o cenário fluir da forma mais limpa possível:
1. O cadastro do Docente ou Aluno agora solicitará que você defina o Login de acesso (ex: "matrícula"), Senha e Nome Completo, que simultaneamente geram a permissão interna de acesso (Tabela `User` atrelada à tabela `Professor` / `Academico`). Tudo bem utilizarmos a integração nativa de segurança do Django?
2. Em `prontuario_paciente.html`, alunos conseguirão ver o balãozinho de feedback/parabéns do professor ao lado da sua evolução. O botão "Remover evolução" irá **sumir** após um professor fechar e "Aprovar" a mesma (Evoluções aprovadas são perpétuas em sistemas médicos reais). Você aprova esse bloqueio?

Módulo de Supervisão Docente 🎓
Sua clínica agora funciona sob autênticos moldes acadêmicos acadêmicos! O módulo foi integralmente codificado e estruturado na base de dados para garantir que tudo operasse conforme as regras de aprovação pelas quais uma instituição de saúde verdadeira trabalha.

O que foi construído nesta Sprint?
1. Cadastros Restritos e Permissões (Menu Lateral Atualizado)
Adicionamos na pasta Cadastros as views Professores e Alunos.
Ao tentar cadastrar um Aluno ou Professor, o sistema vai pedir obrigatoriamente um Usuário de Acesso e uma Senha.
O que o sistema faz por trás: Ele gera a conta master do sistema e atrela ao Aluno/Docente, permitindo que estas pessoas possam finalmente fazer Login Seguro no ClínicaEdu.
2. PEP sob Supervisão (Aguardando...)
Nos Prontuários Eletrônicos criados na aula passada, agora injetamos uma inteligência baseada nos alunos: Toda a evolução inserida nasce obrigatoriamente com o status Aguardando.
Um Aluno Pendente vê do lado do seu nome, na evolução da timeline do paciente, a marca intermitente e amarela indicando que seu resumo clínico ainda não tem valor médico/legal.
Alunos só podem remover uma evolução sua enquanto ela estiver como Pendente. Depois de finalizada, o botão vermelho desaparece pra sempre!
3. A Caixa Verde (Aprovações Pendentes) 🟢
Inseri na linha principal do menu lateral a nova Aba "Supervisão Clínica". Ela só faz sentido aos nossos Docentes.
Lá, haverá a famosa "Pilha de Papéis na Mesa Docente". Todos os prontuários amarelados do Sistema vão chover naquela Inbox.
Todo professor poderá visualizar, entrar e fazer a checagem: ler o que o aluno escreveu, julgar se a conduta dele no procedimento esteve correta, e então imputar uma Nota de 0 a 10 e escrever um Parecer (Comentário Final) pro aluno.
Após o Docente clicar no botão verde de Aprovar Definitivamente, o PEP volta pra timeline com cor Verde Esmeralda mostrando a todos que está finalizado.
Próximo Passo Sugerido
Sugiro você criar pelo sistema logado um Aluno de Teste e um Professor Acadêmico de Teste, e ensaiar a engrenagem (escrever algo = aprovar depois).

Tudo já se encontra no banco de dados consolidado! Qual é a nossa próxima funcionalidade para evoluir o sistema hoje?