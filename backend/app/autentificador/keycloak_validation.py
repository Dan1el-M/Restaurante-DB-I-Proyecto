import os #para obtener las variables de entorno
import requests #para hacer la peticion a keycloak y obtener las claves publicas
from jose import jwt #para validar el token usando la clave publica de keycloak

'''
Este archivo se encarga de validar el token que se recibe en las rutas protegidas.
Primero obtiene la clave pública de Keycloak, luego valida el token usando esa clave.

pasos:
1-recibe algo (un token)
2-sacas las claves publicas de keycloak
3-busca si la clave del token coincide con alguna de las claves publicas
4-si no encuentra la clave, lanza un error
5-si la encuntra la valida usando la clave publica, el issuer, el audience y el algoritmo
6-si todo es correcto devuelve el payload del token, que es la informacion del usuario
'''

#antes no lo descaregaba entonces tecnicamente la validacione era como floja
'''
obtiene el jwt de keycloak
'''
def get_jwks():
	#saca los datos del .env
	keycloak_url = os.getenv("KEYCLOAK_URL")
	realm = os.getenv("KEYCLOAK_REALM")
	
    #crea la url para obtener las claves publicas de keycloak, que es el endpoint de JWKS
	jwks_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
	
    #hace la peticion y reotna el json con las claves publicas
	#validad que la peticion no nvenga vacia
	response = requests.get(jwks_url, timeout=5)
	if not response.ok:
		raise Exception("Failed to fetch JWKS")
	return response.json()


#esto es como lo que haciamos con las API, priemro sacamos la informacion
#luego validamos y despues damos una respuesta
'''
valida el token usando la clave publica de keycloak,
 lo recibe como string,
 lo decodifica y devuelve el payload
 '''
def validate_token(token: str):
	keycloak_url = os.getenv("KEYCLOAK_URL") #saca la url de keycloak del .env
	realm = os.getenv("KEYCLOAK_REALM") # saca el realm del .env
	#esto no termino de entender que obtiene en realidad
	client_id = os.getenv("KEYCLOAK_CLIENT_ID")
	audience = os.getenv("KEYCLOAK_TOKEN_AUDIENCE", "account")

    #contruye la url del issuer
	issuer = f"{keycloak_url}/realms/{realm}"
	#saca las claves publicas de keycloak usando la funciion de arriba
	jwks = get_jwks()
	#Lee el header del token sin validar todavía.
	headers = jwt.get_unverified_header(token)
	#obtiene el kid del header, que es el identificador de la clave que se usó para firmar el token
	kid = headers.get("kid")

    #for para ver si la clave del usuario coincide con las claves que sacamos
	key = None
	for jwk in jwks.get("keys", []):
		if jwk.get("kid") == kid:
			key = jwk
			break

	if not key:
		raise Exception("public key not found")

	# validar el token usando la clave pública obtenida del JWKS endpoint de Keycloak
	payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
    )
	return payload
#nota, podriamos segmentarla más pero si lo hacemos hay que hacer mas archivos para que quede bien