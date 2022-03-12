from setuptools import setup

with open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='ccqt',
    version='0.0.1',
    description='Python Library for cryptocurrency quant trading',
    long_description=readme,
    long_description_content_type='text/markdown',
    #url='',
    author='Yiru Jeon',
    author_email='yiru.jeon@gmail.com',
    keywords=['CryptoCurrency', 'Quant', 'Trading', 'Backtest'],
    #license='MIT',
    python_requires='>=3',
    packages=['ccqt'],
    classifiers=['Programming Language :: Python :: 3'],
    #install_requires=['requests']
)
