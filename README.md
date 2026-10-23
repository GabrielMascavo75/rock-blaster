# Rock Blaster

Jogo controlado por gestos com a webcam: mire com a palma da mão e feche a mão para atirar nas rochas que caem antes que elas atinjam o chão. Feito em Python com OpenCV e MediaPipe.

## Requisitos

- **Webcam** funcionando.
- Windows, Linux ou macOS.
- **Internet na primeira execução** (para baixar o Python e as bibliotecas).

Não é preciso ter o Python instalado: o script de inicialização cuida de tudo.

## Como rodar (jeito rápido)

### Windows

Dê dois cliques em **`jogar.bat`**.

Se aparecer um aviso azul do Windows ("O Windows protegeu o computador"), clique em **Mais informações → Executar assim mesmo**.

### Linux / macOS

Abra um terminal na pasta do jogo e rode:

```
chmod +x jogar.sh
./jogar.sh
```

O `chmod` só é necessário na primeira vez.

### O que o script faz

1. Instala o [uv](https://docs.astral.sh/uv/), um gerenciador de pacotes Python, se ainda não estiver instalado.
2. Baixa o Python 3.12 automaticamente, sem mexer em outros Pythons que você já tenha.
3. Instala as bibliotecas listadas em `requirements.txt`.
4. Abre o jogo.

A **primeira execução demora alguns minutos**, porque o MediaPipe é uma biblioteca grande. Nas próximas vezes, o jogo abre em poucos segundos.

## Instalação manual (alternativa)

Se preferir não usar o script, você precisa do **Python 3.12** (testado com 3.12.10). O Python 3.13 ou mais novo **não funciona**, porque o MediaPipe 0.10.21 não tem pacotes para essas versões. Confira sua versão com `python --version`.

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Linux / macOS)
pip install -r requirements.txt
python rock_blaster.py
```

> No Windows, se tiver mais de uma versão do Python, use `py -3.12 -m venv venv` para criar o ambiente com a 3.12.

Nas próximas vezes, basta ativar o ambiente virtual e rodar `python rock_blaster.py`.

## Como jogar

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

**O script diz que o `uv` não foi encontrado logo depois de instalá-lo**
Feche a janela e rode o script de novo. Em alguns sistemas, o terminal só reconhece programas recém-instalados depois de reaberto.

**O script trava ou falha ao baixar**
Verifique a conexão com a internet. Redes de escola ou empresa às vezes bloqueiam downloads; tente em outra rede.

**`Nao foi possivel acessar a webcam.`**
Feche outros programas que possam estar usando a câmera (Teams, Zoom, Discord, OBS, navegador). Verifique também se a webcam está conectada e habilitada.

**No macOS a câmera não abre**
Dê permissão de câmera ao aplicativo que está rodando o jogo (Terminal, iTerm ou sua IDE) em *Ajustes do Sistema → Privacidade e Segurança → Câmera*, e reinicie o terminal.

**`No matching distribution found for mediapipe==0.10.21`** (instalação manual)
Sua versão do Python não é compatível. Confira com `python --version` dentro do ambiente virtual e recrie o ambiente com o Python 3.12.

**`ModuleNotFoundError: No module named 'cv2'` (ou `mediapipe`)** (instalação manual)
O ambiente virtual provavelmente não está ativado. Ative-o e rode o jogo de novo.

**O jogo está lento ou a mira treme muito**
Melhore a iluminação e feche outros programas pesados. A detecção da mão usa bastante processamento.

## Vídeo demonstrativo

[Clique aqui para assistir ao vídeo do projeto](https://drive.google.com/file/d/13H6VuPZjz3kinmmvOm-lPdIauKaFFwV1/view?usp=sharing)

