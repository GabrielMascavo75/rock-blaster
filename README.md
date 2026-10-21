# Rock Blaster

Jogo controlado por gestos com a webcam: mire com a palma da mão e feche a mão para atirar nas rochas que caem antes que elas atinjam o chão. Feito em Python com OpenCV e MediaPipe.

## Requisitos

- **Python 3.12** (testado com 3.12.10). O Python 3.13 ou mais novo **não funciona**, porque o MediaPipe 0.10.21 não tem pacotes para essas versões.
- **Webcam** funcionando.
- Windows, Linux ou macOS.

Para conferir sua versão do Python:

```
python --version
```

Se aparecer 3.13 ou superior, instale o Python 3.12 em [python.org/downloads](https://www.python.org/downloads/) (procure a versão 3.12.x na lista). No Windows, marque a opção **"Add Python to PATH"** durante a instalação.

## Instalação

Abra um terminal na pasta do jogo e siga os passos.

**1. Crie um ambiente virtual** (isola as bibliotecas do jogo do resto do sistema):

```
python -m venv venv
```

> Se você tiver mais de uma versão do Python instalada no Windows, use `py -3.12 -m venv venv` para garantir que o ambiente seja criado com a 3.12.

**2. Ative o ambiente virtual:**

Windows:
```
venv\Scripts\activate
```

Linux / macOS:
```
source venv/bin/activate
```

Quando estiver ativo, aparece `(venv)` no início da linha do terminal.

**3. Instale as dependências:**

```
pip install -r requirements.txt
```

## Como jogar

Com o ambiente virtual ativado, rode:

```
python rock_blaster.py
```

Nas próximas vezes, basta ativar o ambiente virtual (passo 2) e rodar o comando acima.

### Menu

Leve a mira (que segue a palma da sua mão) até o botão **JOGAR** e **feche a mão**. Também dá para clicar no botão com o mouse ou apertar **ENTER**.

### Controles

| Ação | Gesto / tecla |
|---|---|
| Mirar | Mover a palma da mão aberta |
| Atirar | Fechar a mão (de aberta para fechada) |
| Super bomba | **ESPAÇO** (só com a barra de energia cheia) |
| Pausar | **P** |
| Reiniciar | **R** |
| Voltar ao menu | **M** |
| Mostrar/ocultar os pontos da mão | **H** |
| Sair | **ESC** |

O mouse também funciona: quando nenhuma mão é detectada, a mira segue o cursor e o clique atira.

### Objetos

| Objeto | Como é | O que fazer |
|---|---|---|
| Pedra | Rocha cinza | 1 tiro. Se cair no chão, você perde 1 vida |
| Diamante | Azul e brilhante | 2 tiros. Vale mais pontos e mais energia |
| Jade | Pedra verde com um "+" | 1 tiro. Recupera 1 vida (aparece a partir do nível 2, só quando falta vida) |
| Bomba | Preta com "!" vermelho | **Não atire!** Estourar uma bomba custa 1 vida. Aparece a partir do nível 4 |

Destruir rochas em sequência aumenta o combo (até x5). A barra de energia enche conforme você acerta; quando estiver cheia, aperte ESPAÇO para limpar a tela inteira. Você começa com 5 vidas.

## Dicas para o reconhecimento funcionar bem

- Jogue em um ambiente **bem iluminado**, com a luz vindo da frente (evite janela atrás de você).
- Fique a uns **50 cm a 1 m** da câmera, com a **mão inteira** visível no quadro.
- Mantenha a **palma voltada para a câmera**.
- Um fundo simples, sem muita coisa atrás, ajuda a detecção.
- Para atirar, abra bem a mão e feche de forma clara. Mão "meio aberta" aparece como *parcial* (mira amarela) e não dispara.

A cor da mira mostra o que o jogo está vendo: **verde** = mão aberta, **vermelha** = mão fechada, **amarela** = parcial, **branca** = nenhuma mão detectada.

## Solução de problemas

**`No matching distribution found for mediapipe==0.10.21`**
Sua versão do Python não é compatível. Confira com `python --version` dentro do ambiente virtual e recrie o ambiente com o Python 3.12.

**`Nao foi possivel acessar a webcam.`**
Feche outros programas que possam estar usando a câmera (Teams, Zoom, Discord, OBS, navegador). Verifique também se a webcam está conectada e habilitada.

**No macOS a câmera não abre**
Dê permissão de câmera ao aplicativo que está rodando o jogo (Terminal, iTerm ou sua IDE) em *Ajustes do Sistema → Privacidade e Segurança → Câmera*, e reinicie o terminal.

**`ModuleNotFoundError: No module named 'cv2'` (ou `mediapipe`)**
O ambiente virtual provavelmente não está ativado. Ative-o (passo 2 da instalação) e rode o jogo de novo.

**O jogo está lento ou a mira treme muito**
Melhore a iluminação e feche outros programas pesados. A detecção da mão usa bastante processamento.
