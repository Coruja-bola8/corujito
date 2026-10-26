# SGAUM — Modo Portátil (Pen Drive)

Sistema de Gestão Administrativa da Unidade Militar  
Versão portátil — funciona em qualquer letra de drive

---

## Estrutura do pen drive

```
[PEN DRIVE]\
├── iniciar_portatil.bat       ← CLIQUE AQUI para usar o sistema
├── configurar_portatil.bat    ← Execute UMA VEZ para preparar o pen drive
├── backup_portatil.bat        ← Execute antes de guardar o pen drive
├── README_PORTATIL.txt        ← Este arquivo
│
├── sistema\                   ← Código do SGAUM
│   ├── app.py
│   ├── models.py
│   ├── auth.py
│   ├── blueprints\
│   ├── templates\
│   ├── static\
│   ├── requirements.txt
│   └── instance\
│       └── dados.db           ← SEU BANCO DE DADOS (faça backup deste arquivo!)
│
├── python-portatil\           ← Criado pelo configurar_portatil.bat
│   └── Lib\site-packages\     ← Flask e dependências instaladas aqui
│
└── backups\                   ← Cópias de segurança do banco
```

---

## Primeira configuração (feita uma vez)

1. Conecte o pen drive em um computador COM Python instalado e COM internet
2. Clique duas vezes em `configurar_portatil.bat`
3. Aguarde instalar as dependências (~2-3 minutos)
4. Pronto — o pen drive está configurado

> Se a sua máquina ainda não tem Python:
> - Acesse https://www.python.org/downloads/
> - Baixe Python 3.11 ou superior
> - Durante a instalação, marque "Add Python to PATH"
> - Depois execute o `configurar_portatil.bat`

---

## Uso diário (qualquer máquina, qualquer letra de drive)

1. Conecte o pen drive
2. Clique duas vezes em `iniciar_portatil.bat`
3. Abra o navegador em: **http://localhost:5000**
4. Ao terminar: faça logoff no sistema → feche a janela do terminal

> A máquina onde você for usar precisa ter Python instalado.
> Veja "Máquinas sem Python" abaixo se precisar usar em PC sem Python.

---

## Rotina de backup recomendada

**Diário (ao terminar de usar):**
- Clique em `backup_portatil.bat` — salva uma cópia com data/hora em `backups\`

**Semanal (ao chegar no trabalho/casa):**
- Copie a pasta `backups\` para um HD externo ou nuvem pessoal
- Ou copie diretamente o `sistema\instance\dados.db` para um local seguro

> O arquivo `dados.db` é TUDO — é o seu banco de dados completo.
> Uma cópia dele é suficiente para restaurar o sistema do zero.

---

## Máquinas sem Python instalado

Se você precisar usar o sistema em uma máquina que não tem Python e não
tem permissão para instalar software, a solução é usar o Python Embeddable:

1. Baixe o "Windows embeddable package (64-bit)" em:
   https://www.python.org/downloads/windows/
   (arquivo: python-3.11.x-embed-amd64.zip, ~10MB)

2. Extraia dentro da pasta `python-portatil\` do pen drive

3. Configure o `python311._pth` para incluir as dependências:
   Adicione a linha: `Lib\site-packages`

4. Execute `configurar_portatil.bat` normalmente

Isso torna o sistema 100% independente de qualquer instalação na máquina.

---

## Solução de problemas

**"Python não encontrado"**
→ Python não está instalado ou não está no PATH da máquina
→ Instale Python em https://www.python.org/downloads/ marcando "Add Python to PATH"

**O sistema não abre / erro de módulo**
→ Execute `configurar_portatil.bat` novamente com internet ativa

**Dados sumidos após trocar de máquina**
→ Os dados ficam em `sistema\instance\dados.db` no próprio pen drive
→ Se este arquivo existir, os dados estão lá
→ Verifique se você usou o `iniciar_portatil.bat` (não o `iniciar.bat` antigo)

**Porta 5000 ocupada**
→ Outra aplicação está usando a porta
→ Abra `sistema\app.py` e mude `port=5000` para `port=5001`
→ Acesse http://localhost:5001

**Pen drive lento**
→ Normal para pen drives mais antigos — SQLite em pen drive pode ser lento
→ Se possível, use um pen drive USB 3.0
→ Alternativa: copie a pasta `sistema\` para o HD local ao começar o dia,
  use, e copie o `dados.db` de volta para o pen drive ao terminar

---

## Versões

| Versão | Data     | Mudança                                           |
|--------|----------|---------------------------------------------------|
| 1.1.0  | Ago/2026 | Versão inicial com suporte a modo portátil        |
