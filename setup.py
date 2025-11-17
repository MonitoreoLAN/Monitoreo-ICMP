import setuptools

with open("README.md", 'r') as f:
    long_description = f.read()

with open("requirements.txt") as f:
    install_requires = f.readlines()

setuptools.setup(
    name='Monitoreo',
    version='0.0.1',
    description='Realizar sondeos a hosts mediante ICMP para verificar su estado',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    author='Monitoreo',
    author_email='telepuertogoosealuio@gmail.com',
    url='https://github.com/Monitore1209',
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    python_requires='>=3.9',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
 
