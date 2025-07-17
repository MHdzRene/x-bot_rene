
import twitter_client as tc


t_client = tc.get_twitter_client()
    # Opcional: Agrega tu propia cuenta como authorized para pruebas
t_client.authorized_users.add('StockP_Ai')  # O el username
t_client.monitor_and_respond_mentions()








