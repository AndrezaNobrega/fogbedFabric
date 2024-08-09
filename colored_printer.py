# colored_printer.py

def successln(message):
    """
    Imprime uma mensagem de sucesso em verde com uma linha em branco antes e depois da mensagem.
    
    :param message: A mensagem a ser impressa.
    """
    print_colored_message(message, color='green')

def errorln(message):
    """
    Imprime uma mensagem de erro em vermelho com uma linha em branco antes e depois da mensagem.
    
    :param message: A mensagem a ser impressa.
    """
    print_colored_message(message, color='red')

def warningln(message):
    """
    Imprime uma mensagem de aviso em amarelo com uma linha em branco antes e depois da mensagem.
    
    :param message: A mensagem a ser impressa.
    """
    print_colored_message(message, color='yellow')

def print_colored_message(message, color='white'):
    """
    Imprime uma mensagem com a cor especificada e adiciona uma linha em branco antes da mensagem.
    
    :param message: A mensagem a ser impressa.
    :param color: A cor da mensagem. Pode ser 'red', 'green', 'yellow' ou 'white'.
    """
    # Códigos de cor ANSI
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    
    # Verifica se a cor fornecida é válida
    if color not in colors:
        print("Cor inválida. Usando a cor padrão (branco).")
        color = 'white'
    
    # Imprime uma linha em branco antes da mensagem
    print()
    
    # Imprime a mensagem colorida
    print(f"{colors[color]}{message}{colors['reset']}")
    
    # Imprime uma linha em branco após a mensagem
    print()
