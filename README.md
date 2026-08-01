# NOVA

**Neural Operations & Virtual Assistant** é uma assistente local para macOS,
controlada por texto ou voz. O reconhecimento principal usa Whisper e funciona offline;
nenhum áudio precisa ser enviado para a nuvem.

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

Para encerrar imediatamente sem resposta falada, diga `NOVA, parar`.

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
