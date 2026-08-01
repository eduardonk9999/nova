# NOVA

**Neural Operations & Virtual Assistant** é uma assistente local para macOS,
controlada por texto ou voz. O reconhecimento principal usa Whisper e funciona offline;
nenhum áudio precisa ser enviado para a nuvem.

## Arquitetura de interação 0.2

1. Resposta de voz assíncrona e interrompível com `NOVA, stop`.
2. Palavra de ativação obrigatória no modo de voz.
3. Confiança real do Whisper e confirmação para ações incertas ou sensíveis.
4. Roteador de linguagem natural para variações comuns dos comandos.
5. Contexto de sessão para `repita`, `agora no Claude` e pesquisas de continuação.
6. Integrações verificadas com Codex e Claude, preservando o clipboard.
7. Aplicativo opcional de barra de menus para controlar o processo e consultar logs.

## O que esta primeira versão faz

- abre, fecha e traz aplicativos para frente;
- ajusta o volume do macOS;
- abre o Claude Code no Terminal dentro da pasta do projeto;
- abre o Claude Desktop e seleciona Projects existentes pela interface do aplicativo;
- abre e controla aplicativos como Codex e Claude;
- pesquisa na internet usando o navegador padrão;
- inicia projetos cadastrados em `config/projects.json`;
- descobre projetos em pastas configuradas e detecta Vite/npm, Django e Docker Compose;
- executa comandos de desenvolvimento no Terminal com uma política de segurança;
- envia prompts para Codex e Claude usando a Automação/Acessibilidade do macOS;
- solicita pesquisas com fontes diretamente ao Codex por comandos como `pesquise X no Codex`;
- aceita `pesquise no Codex X` e normaliza termos ditados como `agá dois ó` para `H2O`;
- aceita a ordem natural `NOVA, no Codex, busque sobre X` e a transcrição `pesquisa sobre X`;
- silencia o Mac e salva capturas de tela por voz;
- informa as horas;
- responde em voz alta usando a voz nativa do macOS;
- aceita comandos digitados mesmo sem as dependências de áudio.

## Início rápido

Recomenda-se Python 3.11, 3.12 ou 3.13, pois bibliotecas de áudio podem demorar a
oferecer suporte a versões recém-lançadas do Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
nova
```

Experimente: `NOVA, abra o Safari`, `feche o Spotify`, `volume 30`, `ajuda`.

## Ativar comandos de voz offline

```bash
pip install -e '.[voice]'
mkdir -p models
```

Instale `whisper.cpp` pelo Homebrew e coloque o modelo multilíngue `ggml-small.bin`
em `models/whisper/`. Depois execute:

```bash
nova --voice
```

O Vosk antigo continua disponível como fallback com `nova --voice --engine vosk`.

Para encerrar imediatamente sem resposta falada, diga `NOVA, stop` ou `NOVA, parar`.

No modo de voz, todos os demais comandos precisam começar com `NOVA`. Conversas
ambientes sem a palavra de ativação são transcritas localmente e ignoradas. A fala
é executada de forma assíncrona, permitindo que `NOVA, stop` interrompa a resposta.

Também é possível dizer apenas `NOVA`, esperar `Pois não?` e falar um comando nos
8 segundos seguintes. A janela aceita somente um comando e fecha automaticamente.

Nome, palavra de ativação, voz feminina e sensibilidade do microfone ficam em
`config/settings.json`, sem necessidade de alterar o código Python.

Antes de enviar texto a Codex ou Claude, a NOVA confirma que o aplicativo existe
e que a permissão de Acessibilidade está ativa. O envio preserva o conteúdo anterior
da área de transferência e informa claramente quando uma permissão está faltando.

## Barra de menus

```bash
pip install -e '.[desktop]'
nova-menubar
```

O ícone `✦` permite iniciar e parar a NOVA, acompanhar o estado e abrir configurações,
log ou projeto sem manter uma janela de Terminal aberta.

Na primeira execução, o macOS pedirá acesso ao microfone. Para controlar outros
aplicativos, talvez também peça autorização em **Ajustes do Sistema → Privacidade e
Segurança → Automação**.

## Personalizar aplicativos

Edite `config/apps.json` para incluir a forma falada e o nome exato do aplicativo:

```json
"whatsapp": "WhatsApp"
```

## Testes

```bash
python -m pytest
```

O executor usa argumentos separados ao chamar ferramentas do sistema e mantém os
apelidos em configuração, evitando executar comandos de shell falados diretamente.
