from flask import redirect


def anexar_query_string(destino, query_string):
    if not query_string:
        return destino

    if isinstance(query_string, bytes):
        query_string = query_string.decode()

    return f"{destino}?{query_string}"


def redirecionar_com_query_string(request, destino):
    return redirect(anexar_query_string(destino, getattr(request, "query_string", b"")))
