import time
from twitter_client import TwitterClient

def main():
    tc = TwitterClient()
    print('Primer análisis (debe generar):')
    result1 = tc.generate_ai_analysis('Apple', 'AAPL')
    print(result1)
    print('\nSegundo análisis inmediato (debe usar caché):')
    result2 = tc.generate_ai_analysis('Apple', 'AAPL')
    print(result2)
    print('\n¿Resultado igual? ', result1 == result2)
    print('\nEsperando 11 minutos para forzar expiración de caché...')
    time.sleep(5)  # Cambia a 660 para prueba real (11 min), aquí solo 5 seg para demo
    print('\nTercer análisis (debe regenerar):')
    result3 = tc.generate_ai_analysis('Apple', 'AAPL')
    print(result3)
    print('\n¿Resultado igual al primero? ', result1 == result3)

if __name__ == '__main__':
    main()
import time
from twitter_client import TwitterClient

def main():
    tc = TwitterClient()
    print('Primer análisis (debe generar):')
    result1 = tc.generate_ai_analysis('Apple', 'AAPL')
    print(result1)
    print('\nSegundo análisis inmediato (debe usar caché):')
    result2 = tc.generate_ai_analysis('Apple', 'AAPL')
    print(result2)
    print('\n¿Resultado igual? ', result1 == result2)
    print('\nEsperando 11 minutos para forzar expiración de caché...')
    time.sleep(5)  # Cambia a 660 para prueba real (11 min), aquí solo 5 seg para demo
    print('\nTercer análisis (debe regenerar):')
    result3 = tc.generate_ai_analysis('Apple', 'AAPL')
    print(result3)
    print('\n¿Resultado igual al primero? ', result1 == result3)

if __name__ == '__main__':
    main()
