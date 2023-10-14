from util import ApplicationContext

context = ApplicationContext()
print(context.options)
result = context.db.execute("SELECT * FROM books")
print(result.fetchone())
context.cleanup()