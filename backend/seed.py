
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.database import SessionLocal, init_db
from backend.models import (
    University, DegreeProgram, Course,
    Skill, CourseSkill, Occupation, SkillOccupation
)



def get_or_create(db: Session, model, where: dict, values: dict = None):
    instance = db.execute(select(model).filter_by(**where)).scalar_one_or_none()

    if instance and values:
        for k, v in values.items():
            if getattr(instance, k, None) in (None, "", []):
                setattr(instance, k, v)
        return instance

    if instance:
        return instance

    instance = model(**{**where, **(values or {})})
    db.add(instance)
    db.flush()
    return instance



GREEK_UNI_DATA = [
    {
        "name": "National and Kapodistrian University of Athens",
    "programs": [
        {
            "type": "BSc", "title": "Informatics and Telecommunications", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Programming", "Procedural programming using C, data types and control flow", 1, 7, "Mandatory"),
                ("Discrete Mathematics", "Logic, sets, functions, and graph theory foundations", 1, 6, "Mandatory"),
                ("Data Structures", "Analysis of stacks, queues, trees, and heaps", 2, 7, "Mandatory"),
                ("Computer Architecture", "Logic design, instruction set architecture and pipelining", 3, 6, "Mandatory"),
                ("Operating Systems", "Kernel structures, multitasking, and memory management", 4, 7, "Mandatory"),
                ("Algorithms and Complexity", "Sorting, searching, and NP-completeness theory", 4, 7, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Medicine", "lang": "Greek", "dur": "12", "ects": "360",
            "courses": [
                ("Medical Physics", "Physics of ionizing radiation and medical imaging principles", 1, 5, "Mandatory"),
                ("Anatomy I", "Systemic anatomy of the human musculoskeletal system", 1, 8, "Mandatory"),
                ("Biochemistry I", "Molecular structure of proteins and enzymatic catalysis", 2, 6, "Mandatory"),
                ("Physiology I", "Cellular physiology and neuromuscular function", 3, 8, "Mandatory"),
                ("Histology and Embryology I", "Microscopic anatomy of tissues and early development", 2, 6, "Mandatory"),
                ("Pharmacology I", "General principles of pharmacokinetics and dynamics", 5, 6, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Law", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Constitutional Law", "The organization of the State and fundamental rights", 1, 7, "Mandatory"),
                ("General Principles of Civil Law", "Legal capacity, transactions, and rights", 1, 8, "Mandatory"),
                ("Criminal Law (General Part)", "Theory of crime and punishment foundations", 2, 7, "Mandatory"),
                ("International Public Law", "Sources of international law and sovereign relations", 3, 6, "Mandatory"),
                ("Administrative Law", "Structure of public administration and legal acts", 3, 7, "Mandatory")
            ]
        },
        {
            "type": "MSc", "title": "Data Science and Information Technologies", "lang": "English", "dur": "4", "ects": "120",
            "courses": [
                ("Statistical Learning", "Regression, classification, and resampling methods", 1, 6, "Mandatory"),
                ("Data Mining", "Pattern discovery, clustering, and association rules", 1, 6, "Mandatory"),
                ("Machine Learning", "Neural networks, SVMs, and ensemble learning", 2, 8, "Mandatory"),
                ("Big Data Management", "NoSQL databases and distributed processing with Spark", 2, 6, "Mandatory"),
                ("Deep Learning", "CNNs, RNNs, and generative adversarial networks", 3, 6, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "English Language and Literature", "lang": "English", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Linguistics", "Scientific study of language: Phonetics to Syntax", 1, 6, "Mandatory"),
                ("Introduction to Literature", "Analysis of literary genres and critical terminology", 1, 6, "Mandatory"),
                ("English Phonetics", "Articulation of speech sounds and transcription", 2, 6, "Mandatory"),
                ("Survey of English Literature I", "Literature from the Middle Ages to the Restoration", 2, 6, "Mandatory"),
                ("Second Language Acquisition", "Theories on how non-native languages are learned", 5, 6, "Mandatory")
            ]
        }
	]
    },
{
"name": "University of Macedonia",
        "programs": [
            {
                "type": "BSc", "title": "Applied Informatics", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Introduction to Programming", "Foundations of procedural programming and logic", 1, 6, "Mandatory"),
                    ("Object-Oriented Programming", "Java-based OOP principles and design patterns", 2, 7, "Mandatory"),
                    ("Data Structures", "Abstract data types, trees, and searching algorithms", 3, 6, "Mandatory"),
                    ("Database Systems", "Relational models, SQL and database design", 4, 6, "Mandatory"),
                    ("Computer Networks", "Network architecture, OSI model and TCP/IP", 5, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Business Administration", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Principles of Management", "Basic management theories and organizational structure", 1, 6, "Mandatory"),
                    ("Principles of Marketing", "Consumer behavior and the marketing mix", 2, 6, "Mandatory"),
                    ("Human Resource Management", "Strategic HR, recruitment and performance appraisal", 5, 6, "Mandatory"),
                    ("Financial Management", "Capital budgeting and financial analysis", 4, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Economics", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Microeconomics I", "Price theory and consumer behavior", 1, 6, "Mandatory"),
                    ("Macroeconomics I", "National income and employment models", 2, 6, "Mandatory"),
                    ("Econometrics I", "Statistical methods and linear regression in economics", 5, 7, "Mandatory"),
                    ("Public Finance", "State budget and fiscal policy", 4, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Accounting and Finance", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Financial Accounting I", "Double-entry bookkeeping and financial statements", 1, 6, "Mandatory"),
                    ("Cost Accounting", "Cost behavior and product costing systems", 3, 6, "Mandatory"),
                    ("Auditing", "Principles of external and internal auditing", 7, 6, "Mandatory"),
                    ("Banking Management", "Commercial banking operations and risk", 6, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "International and European Studies", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("International Relations Theory", "Realism, Liberalism and Constructivism in global politics", 1, 6, "Mandatory"),
                    ("Public International Law", "Legal frameworks governing sovereign states", 3, 6, "Mandatory"),
                    ("European Integration", "History and institutional evolution of the EU", 2, 6, "Mandatory"),
                    ("Diplomatic History", "History of international relations since 1815", 4, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Balkan, Slavic and Oriental Studies", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("History of the Balkan Peninsula", "Political and social history of the Balkans", 1, 6, "Mandatory"),
                    ("Political Economy of South-East Europe", "Economic development in the Balkan region", 4, 6, "Mandatory"),
                    ("Social Anthropology of the Balkans", "Cultural studies and ethnicity in SE Europe", 3, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Educational and Social Policy", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Special Education Foundations", "Introduction to disabilities and educational support", 1, 6, "Mandatory"),
                    ("Lifelong Learning", "Theories of adult education and training", 2, 6, "Mandatory"),
                    ("Educational Psychology", "Cognitive development and learning theories", 3, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Music Science and Art", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Harmony I", "Tonal harmony and voice leading", 1, 5, "Mandatory"),
                    ("History of Western Music", "Evolution of music from Antiquity to Baroque", 1, 5, "Mandatory"),
                    ("Ethnomusicology", "Study of traditional and world music systems", 4, 6, "Mandatory")
                ]
            }
        ]
    },
    {
    "name": "Aristotle University of Thessaloniki",
    "programs": [
        {
            "type": "BSc", "title": "Electrical and Computer Engineering", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Linear Algebra", "Vector spaces, matrices, determinants and systems of linear equations", 1, 6, "Mandatory"),
                ("Calculus I", "Differential and integral calculus of one variable", 1, 7, "Mandatory"),
                ("Introductory Programming", "Foundations of programming using the C language", 1, 7, "Mandatory"),
                ("Digital Systems", "Boolean algebra, logic gates, and combinational/sequential circuits", 2, 6, "Mandatory"),
                ("Electric Circuits I", "DC circuits, Kirchhoff laws, and network theorems", 2, 6, "Mandatory"),
                ("Object-Oriented Programming", "Class hierarchies, inheritance and polymorphism in C++", 3, 6, "Mandatory"),
                ("Signals and Systems", "Continuous and discrete-time signals, Fourier and Laplace transforms", 4, 7, "Mandatory"),
                ("Computer Architecture", "CPU organization, memory hierarchy and I/O systems", 5, 6, "Mandatory"),
                ("Database Systems", "Relational model, SQL and database management", 6, 6, "Mandatory"),
                ("Control Systems", "Feedback control, stability analysis and PID controllers", 6, 6, "Mandatory"),
                ("Machine Learning", "Neural networks, clustering and supervised learning models", 9, 5, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Physics", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("General Physics I: Mechanics", "Newtonian mechanics, kinematics and dynamics of particles", 1, 7, "Mandatory"),
                ("Mathematical Methods for Physics I", "Complex numbers, vector calculus and series", 1, 7, "Mandatory"),
                ("General Physics II: Electromagnetism", "Electric fields, Gauss law, and electric potential", 2, 7, "Mandatory"),
                ("Thermodynamics", "Heat, work, and the laws of thermodynamics", 3, 6, "Mandatory"),
                ("Quantum Mechanics I", "Schrodinger equation and operators in Hilbert space", 5, 7, "Mandatory"),
                ("Atomic Physics", "Hydrogen atom, spin and multi-electron atoms", 4, 6, "Mandatory"),
                ("Solid State Physics I", "Crystal structures, lattice vibrations and electrons in solids", 6, 6, "Mandatory"),
                ("Nuclear Physics", "Radioactivity, nuclear models and reactions", 6, 6, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Architecture", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Architectural Design I", "Introduction to space, form and function in design", 1, 9, "Mandatory"),
                ("Descriptive Geometry", "Projection methods and 3D geometric representation", 1, 4, "Mandatory"),
                ("History of Architecture I", "Architectural evolution from prehistory to early Christian era", 1, 4, "Mandatory"),
                ("Visual Arts I", "Freehand drawing and color theory foundations", 1, 4, "Mandatory"),
                ("Construction Technology I", "Materials and masonry construction methods", 3, 5, "Mandatory"),
                ("Urban Design I", "Principles of urban planning and city layout analysis", 5, 6, "Mandatory"),
                ("Restoration of Monuments", "Theories and techniques for preserving historical buildings", 7, 5, "Mandatory"),
                ("Landscape Architecture", "Design of open spaces and integration with nature", 8, 5, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Veterinary Medicine", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Veterinary Anatomy I", "Osteology, arthrology and myology of domestic animals", 1, 8, "Mandatory"),
                ("Animal Biochemistry", "Metabolic pathways and enzyme function in animals", 1, 6, "Mandatory"),
                ("Veterinary Histology and Embryology", "Microscopic anatomy and development of animal tissues", 2, 7, "Mandatory"),
                ("Veterinary Physiology I", "Neurophysiology and cardiovascular system functions", 2, 7, "Mandatory"),
                ("Veterinary Microbiology", "General bacteriology and virology relevant to animal health", 3, 6, "Mandatory"),
                ("Pharmacology", "Drug actions, dosing and therapeutics in veterinary practice", 5, 6, "Mandatory"),
                ("Diagnostic Imaging", "Radiology, ultrasound and advanced imaging for animals", 6, 5, "Mandatory"),
                ("Small Animal Surgery I", "Anesthesia and soft tissue surgery for pets", 8, 7, "Mandatory")
            ]
        },
        {
            "type": "MSc", "title": "Digital Media, Communication and Journalism", "lang": "English", "dur": "3", "ects": "90",
            "courses": [
                ("Media and Communication in the Global Era", "Theories of mass communication and globalization impacts", 1, 10, "Mandatory"),
                ("Research Methods for Social Sciences", "Quantitative and qualitative analysis in media studies", 1, 10, "Mandatory"),
                ("Data Journalism and Visualization", "Interactive storytelling and infographics using big data", 2, 10, "Mandatory"),
                ("Digital Media and Politics", "The role of social media in political campaigns and activism", 2, 10, "Mandatory"),
                ("Master's Thesis", "Independent research on a digital media topic", 3, 30, "Mandatory")
            ]
        }
    ]
},
   {
    "name": "National Technical University of Athens",
    "programs": [
        {
            "type": "BSc", "title": "Civil Engineering", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Mathematical Analysis & Linear Algebra", "Calculus and vector spaces for engineers", 1, 8, "Mandatory"),
                ("Mechanics of Solid Bodies", "Statics, force systems, and equilibrium of rigid bodies", 1, 6, "Mandatory"),
                ("Engineering Geology", "Geological principles and their application in civil works", 1, 5, "Mandatory"),
                ("Mechanics of Deformable Bodies", "Stress, strain, and axial loading in structures", 2, 7, "Mandatory"),
                ("Fluid Mechanics", "Hydrostatics, hydrodynamics, and pipe flow", 4, 6, "Mandatory"),
                ("Soil Mechanics I", "Physical properties, classification, and effective stress of soils", 5, 6, "Mandatory"),
                ("Reinforced Concrete I", "Analysis and design of concrete beams and columns", 7, 7, "Mandatory"),
                ("Steel Structures I", "Design of steel members and connections under tension/compression", 7, 6, "Mandatory"),
                ("Transportation Engineering", "Principles of highway and traffic engineering", 6, 6, "Mandatory"),
                ("Hydraulics", "Open channel flow and hydraulic structures", 5, 6, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Mechanical Engineering", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Technical Drawing", "Principles of manual and computer-aided drafting", 1, 5, "Mandatory"),
                ("Programming for Engineers", "Foundations of C programming and numerical algorithms", 1, 6, "Mandatory"),
                ("Thermodynamics I", "Properties of pure substances, 1st and 2nd laws", 3, 6, "Mandatory"),
                ("Machine Elements I", "Design of joints, springs, and power screws", 5, 7, "Mandatory"),
                ("Heat Transfer I", "Conduction, convection, and radiation fundamentals", 6, 6, "Mandatory"),
                ("Internal Combustion Engines I", "Cycles, combustion, and performance of SI and Diesel engines", 7, 6, "Mandatory"),
                ("Manufacturing Technology I", "Casting, forming, and welding processes", 4, 6, "Mandatory"),
                ("Control Systems", "Transfer functions, stability, and PID controllers", 6, 6, "Mandatory"),
                ("Steam Boilers", "Design and operation of steam generation systems", 8, 5, "Optional"),
                ("Computational Fluid Dynamics (CFD)", "Numerical solutions for complex flow fields", 9, 6, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Chemical Engineering", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Inorganic Chemistry", "Atomic structure, bonding, and main group elements", 1, 6, "Mandatory"),
                ("Introduction to Chemical Engineering", "Mass and energy balances in process systems", 1, 5, "Mandatory"),
                ("Organic Chemistry I", "Structure and reactivity of aliphatic and aromatic compounds", 2, 7, "Mandatory"),
                ("Physical Chemistry I", "Thermodynamics of chemical systems and phase equilibria", 3, 6, "Mandatory"),
                ("Transport Phenomena I", "Momentum transfer and fluid mechanics in pipes", 4, 7, "Mandatory"),
                ("Chemical Reaction Engineering I", "Kinetics and design of ideal chemical reactors", 6, 7, "Mandatory"),
                ("Unit Operations I", "Distillation, absorption, and extraction processes", 5, 6, "Mandatory"),
                ("Safety of Industrial Installations", "Risk assessment and safety protocols in chemical plants", 9, 5, "Mandatory"),
                ("Biotechnology", "Microbiological processes and bioreactor design", 8, 6, "Optional"),
                ("Polymer Science", "Synthesis, properties, and processing of plastics", 7, 6, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Applied Mathematical and Physical Sciences", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Physics I (Mechanics)", "Newtonian mechanics and oscillations for science majors", 1, 7, "Mandatory"),
                ("Mathematical Analysis I", "Calculus of real functions and sequences", 1, 8, "Mandatory"),
                ("Scientific Computing", "Programming for physical simulation and data analysis", 2, 6, "Mandatory"),
                ("Quantum Mechanics I", "Wave functions, operators, and the Schrodinger equation", 5, 7, "Mandatory"),
                ("Electromagnetism I", "Electrostatics, magnetostatics, and Faraday's law", 3, 7, "Mandatory"),
                ("Numerical Analysis I", "Error analysis and interpolation methods", 4, 6, "Mandatory"),
                ("Functional Analysis", "Banach and Hilbert spaces with applications in physics", 7, 7, "Mandatory"),
                ("Statistical Physics", "Laws of thermodynamics from a microscopic perspective", 6, 6, "Mandatory"),
                ("General Relativity", "Curvature, black holes, and cosmological models", 9, 6, "Optional"),
                ("Mathematical Logic", "Propositional and predicate calculus foundations", 8, 5, "Optional")
            ]
        }
    ]
},
    {
        "name": "Athens University of Economics and Business",
        "programs": [
            {
                "type": "BSc", "title": "Economics", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Microeconomics I", "Consumer theory, preferences, and utility maximization", 1, 6, "Mandatory"),
                    ("Mathematics I", "Calculus, sequences, and series for economic analysis", 1, 6, "Mandatory"),
                    ("Financial Accounting", "Principles of accounting and financial statement preparation", 1, 6, "Mandatory"),
                    ("Macroeconomics I", "National accounts, inflation, and the labor market", 2, 6, "Mandatory"),
                    ("Statistics I", "Probability theory and descriptive statistics for economists", 2, 6, "Mandatory"),
                    ("Econometrics I", "Simple and multiple linear regression models", 5, 6, "Mandatory"),
                    ("Public Economics", "Government intervention, taxation, and public goods", 6, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Business Administration", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Business Studies", "Introduction to organizational structures and business functions", 1, 6, "Mandatory"),
                    ("Principles of Management", "Planning, organizing, and leadership in modern firms", 2, 6, "Mandatory"),
                    ("General Mathematics of Finance", "Interest rates, annuities, and loan amortization", 1, 6, "Mandatory"),
                    ("Marketing Management", "Product strategy, pricing, and market segmentation", 3, 6, "Mandatory"),
                    ("Strategic Management", "Case studies on competitive advantage and industry analysis", 7, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Accounting and Finance", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Financial Accounting II", "Advanced accounting for corporations and partnerships", 2, 6, "Mandatory"),
                    ("Corporate Finance", "Capital budgeting and investment appraisal techniques", 3, 6, "Mandatory"),
                    ("Cost Accounting", "Product costing, budgeting, and variance analysis", 4, 6, "Mandatory"),
                    ("Auditing", "Standards, ethics, and procedures for financial audits", 6, 6, "Mandatory"),
                    ("Banking Management", "Asset-liability management and credit risk in banking", 7, 6, "Mandatory")
                ]
            },
            {
                "type": "MSc", "title": "Data Science", "lang": "English", "dur": "3", "ects": "90",
                "courses": [
                    ("Machine Learning and Computational Techniques", "Math foundations of ML, optimization, and regression", 1, 8, "Mandatory"),
                    ("Large Scale Data Management", "Architecture of Big Data systems and NoSQL", 1, 8, "Mandatory"),
                    ("Statistical Learning", "Regularization, trees, and ensemble methods", 2, 8, "Mandatory"),
                    ("Recommender Systems", "Collaborative filtering and content-based recommendation", 2, 5, "Optional"),
                    ("Deep Learning", "CNNs, RNNs, and applications in Computer Vision/NLP", 2, 6, "Optional")
                ]
            }
        ]
    },
    {
        "name": "University of Patras",
        "programs": [
            {
                "type": "BSc", "title": "Computer Engineering and Informatics", "lang": "Greek", "dur": "10", "ects": "300",
                "courses": [
                    ("Discrete Mathematics", "Logic, set theory, and graph theory foundations", 1, 6, "Mandatory"),
                    ("Introduction to Programming", "Procedural programming and algorithms using C", 1, 6, "Mandatory"),
                    ("Linear Algebra", "Matrix theory and vector spaces for engineering", 1, 6, "Mandatory"),
                    ("Digital Design", "Logic gates, minimization, and synchronous circuits", 2, 6, "Mandatory"),
                    ("Object-Oriented Programming", "Design patterns and software development in Java", 2, 7, "Mandatory"),
                    ("Introduction to Algorithms", "Sorting, searching, and complexity analysis", 3, 6, "Mandatory"),
                    ("Operating Systems", "Process scheduling, memory management, and file systems", 5, 6, "Mandatory"),
                    ("Artificial Intelligence", "Search algorithms, knowledge representation, and expert systems", 6, 6, "Mandatory"),
                    ("Computer Networks", "Protocols, routing, and network layer architecture", 6, 6, "Mandatory"),
                    ("Diploma Thesis", "Year-long research and implementation project", 10, 30, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Biology", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("The Science of Biology", "Introduction to biological levels of organization", 1, 8, "Mandatory"),
                    ("General Chemistry", "Inorganic and organic chemistry for life sciences", 1, 8, "Mandatory"),
                    ("Biochemistry I", "Structure and function of biomolecules and enzymes", 3, 8, "Mandatory"),
                    ("Genetics I", "Mendelian genetics and chromosome theory", 4, 8, "Mandatory"),
                    ("Developmental Biology", "Cell differentiation and embryonic development", 6, 6, "Mandatory"),
                    ("Evolution", "Molecular evolution and phylogenetic analysis", 6, 6, "Mandatory"),
                    ("Ecology I", "Population dynamics and ecosystem energetics", 6, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Geology", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Mineralogy I", "Crystallography and physical properties of minerals", 1, 6, "Mandatory"),
                    ("Planet Earth", "Earth's interior, plate tectonics, and surface processes", 1, 6, "Mandatory"),
                    ("Principles of Oceanography", "Physical, chemical, and biological oceanography", 1, 5, "Mandatory"),
                    ("Structural Geology", "Deformation of rocks, faults, and folds", 5, 6, "Mandatory"),
                    ("Sedimentology", "Formation, transport, and deposition of sediments", 5, 6, "Mandatory"),
                    ("Geophysics", "Seismic, gravity, and magnetic methods for earth exploration", 6, 6, "Mandatory")
                ]
            }
        ]
    },
    {
    "name": "University of Piraeus",
    "programs": [
        {
            "type": "BSc", "title": "Digital Systems", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Digital Systems", "Foundations of digital logic, binary systems, and hardware components", 1, 6, "Mandatory"),
                ("Programming I", "Introduction to procedural programming and problem solving using C/C++", 1, 6, "Mandatory"),
                ("Mathematics for Digital Systems I", "Calculus, limits, and sequences for technical applications", 1, 6, "Mandatory"),
                ("Object-Oriented Programming", "Software development principles using Java and design patterns", 2, 6, "Mandatory"),
                ("Computer Networks", "Architecture of data communication, OSI model, and TCP/IP stack", 3, 6, "Mandatory"),
                ("Database Systems", "Design of relational databases, ER diagrams, and SQL", 4, 6, "Mandatory"),
                ("Information Systems Security", "Principles of cryptography, network security, and risk assessment", 5, 6, "Mandatory"),
                ("Wireless Communications", "Propagation, modulation techniques, and mobile network standards", 6, 6, "Mandatory"),
                ("Network Management", "Administration of enterprise networks and monitoring tools", 7, 6, "Mandatory"),
                ("Electronic Entrepreneurship", "Business models and digital transformation in the modern economy", 8, 6, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Banking and Financial Management", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Financial Accounting I", "Double-entry bookkeeping and preparation of financial statements", 1, 6, "Mandatory"),
                ("Microeconomic Analysis", "Consumer behavior, market structures, and price theory", 1, 6, "Mandatory"),
                ("Mathematics for Business I", "Linear algebra and calculus applied to financial models", 1, 6, "Mandatory"),
                ("Financial Management I", "Capital budgeting, time value of money, and investment appraisal", 3, 6, "Mandatory"),
                ("Macroeconomic Analysis", "National income, inflation, and fiscal/monetary policy", 2, 6, "Mandatory"),
                ("Money and Banking", "The role of central banks and the commercial banking system", 4, 6, "Mandatory"),
                ("Investments", "Portfolio theory, CAPM, and security analysis", 5, 6, "Mandatory"),
                ("Financial Derivatives", "Options, futures, and swaps pricing and hedging strategies", 6, 6, "Mandatory"),
                ("Risk Management", "Measurement and management of market, credit, and operational risk", 7, 6, "Mandatory"),
                ("International Finance", "Exchange rates, balance of payments, and global capital markets", 8, 6, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Maritime Studies", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Shipping", "Overview of the global maritime industry and shipping markets", 1, 6, "Mandatory"),
                ("General Principles of Law", "Introduction to legal concepts and civil law basics", 1, 6, "Mandatory"),
                ("Maritime History", "Evolution of shipping from antiquity to the modern era", 1, 6, "Mandatory"),
                ("Maritime Economics", "Supply and demand in shipping, freight rates, and market cycles", 3, 6, "Mandatory"),
                ("Management of Shipping Companies", "Organizational structure and strategy of maritime firms", 4, 6, "Mandatory"),
                ("Chartering", "Voyage and time charterparty analysis and negotiations", 5, 6, "Mandatory"),
                ("Maritime Law", "Legal framework for carriage of goods by sea and ship arrest", 6, 6, "Mandatory"),
                ("Marine Insurance", "P&I clubs, hull and machinery insurance, and claims", 5, 6, "Mandatory"),
                ("Port Management", "Operation, economics, and logistics of modern port terminals", 7, 6, "Mandatory"),
                ("Ship Technology", "Basic ship construction, stability, and propulsion systems", 2, 6, "Mandatory")
            ]
        }
    ]
},
    {
    "name": "University of Crete",
    "programs": [
        {
            "type": "BSc", "title": "Computer Science", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("CS-100: Introduction to Computer Science", "General overview of computing, hardware, and binary logic", 1, 6, "Mandatory"),
                ("CS-150: Programming", "Problem solving and procedural programming using the C language", 1, 7, "Mandatory"),
                ("CS-225: Discrete Mathematics", "Sets, functions, graph theory, and proof techniques", 1, 6, "Mandatory"),
                ("CS-120: Digital Design", "Boolean algebra, gates, and combinational/sequential logic", 2, 6, "Mandatory"),
                ("CS-240: Data Structures", "Implementation of lists, stacks, trees, and hash tables", 2, 7, "Mandatory"),
                ("CS-252: Object-Oriented Programming", "Principles of OOP, classes, and inheritance using C++", 3, 6, "Mandatory"),
                ("CS-255: Computer Architecture", "CPU design, instruction sets, and memory hierarchy", 4, 6, "Mandatory"),
                ("CS-345: Operating Systems", "Process management, concurrency, and virtual memory", 5, 6, "Mandatory"),
                ("CS-335: Computer Networks", "Protocol layers, TCP/IP, and wireless communications", 6, 6, "Mandatory"),
                ("CS-340: Languages and Compilers", "Lexical analysis, parsing, and code generation", 6, 6, "Mandatory"),
                ("CS-463: Information Retrieval", "Search engines, indexing, and ranking algorithms", 7, 6, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Mathematics and Applied Mathematics", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Calculus I", "Limits, continuity, and derivatives of real functions", 1, 8, "Mandatory"),
                ("Linear Algebra I", "Vector spaces, matrices, and systems of linear equations", 1, 8, "Mandatory"),
                ("Calculus II", "Integrals, sequences, and series of functions", 2, 8, "Mandatory"),
                ("Linear Algebra II", "Inner product spaces and eigenvalue problems", 2, 8, "Mandatory"),
                ("Ordinary Differential Equations", "First and second order equations and applications", 3, 7, "Mandatory"),
                ("Introduction to Algebraic Structures", "Basic group, ring, and field theory", 3, 7, "Mandatory"),
                ("Real Analysis", "Metric spaces, topology, and continuity theory", 4, 8, "Mandatory"),
                ("Numerical Analysis", "Error analysis and numerical solutions of equations", 5, 7, "Mandatory"),
                ("Probability Theory", "Random variables, distributions, and law of large numbers", 4, 7, "Mandatory"),
                ("Complex Analysis", "Holomorphic functions, contour integration, and residues", 6, 7, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Psychology", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Psychology I", "Foundations of psychological science and historical schools", 1, 6, "Mandatory"),
                ("Developmental Psychology I", "Childhood development: cognitive and social aspects", 1, 6, "Mandatory"),
                ("Cognitive Psychology I", "Study of perception, attention, and memory", 2, 6, "Mandatory"),
                ("Social Psychology I", "Attitudes, social influence, and group behavior", 2, 6, "Mandatory"),
                ("Statistics I", "Descriptive statistics and probability in social sciences", 1, 6, "Mandatory"),
                ("Experimental Psychology", "Design and execution of psychological experiments", 3, 6, "Mandatory"),
                ("Biopsychology", "Biological foundations of behavior and the nervous system", 3, 6, "Mandatory"),
                ("Clinical Psychology I", "Theories of psychopathology and diagnostic methods", 5, 6, "Mandatory"),
                ("Psychometrics", "Theory and construction of psychological tests", 4, 6, "Mandatory"),
                ("Personality Psychology", "Major theories and assessment of individual differences", 4, 6, "Mandatory")
            ]
        }
    ]
},
    {
    "name": "Technical University of Crete",
    "programs": [
        {
            "type": "BSc", "title": "Production Engineering and Management", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("General Chemistry", "Basic principles of chemistry and properties of matter for engineers", 1, 5, "Mandatory"),
                ("Calculus I", "Limits, continuity, and differential calculus of one variable", 1, 7, "Mandatory"),
                ("Physics I", "Classical mechanics: kinematics, dynamics, and energy", 1, 6, "Mandatory"),
                ("Introduction to Manufacturing", "Basic processes and materials used in industrial manufacturing", 2, 5, "Mandatory"),
                ("Thermodynamics", "Energy, heat, and the laws of thermodynamics for engineering systems", 3, 6, "Mandatory"),
                ("Operations Research I", "Linear programming and optimization algorithms for decision making", 5, 7, "Mandatory"),
                ("Quality Control", "Statistical methods for quality assurance in production lines", 6, 6, "Mandatory"),
                ("CAD/CAM Systems", "Computer-aided design and manufacturing with laboratory practice", 7, 6, "Mandatory"),
                ("Supply Chain Management", "Logistics, inventory control, and distribution networks", 8, 6, "Mandatory"),
                ("Project Management", "Planning, scheduling, and controlling engineering projects", 7, 5, "Mandatory"),
                ("Robotics in Production", "Automation and robotic systems in the manufacturing environment", 9, 5, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Electrical and Computer Engineering", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Linear Algebra", "Vector spaces, matrices, and linear transformations", 1, 6, "Mandatory"),
                ("Structured Programming", "Problem solving and programming using the C language", 1, 7, "Mandatory"),
                ("Physics II: Electromagnetism", "Electric fields, magnetism, and Maxwell's equations", 2, 6, "Mandatory"),
                ("Object-Oriented Programming", "Design principles and software engineering using C++", 2, 6, "Mandatory"),
                ("Electronics I", "Semiconductors, diodes, and transistor circuit analysis", 3, 6, "Mandatory"),
                ("Signals and Systems", "Continuous and discrete-time signal processing foundations", 4, 7, "Mandatory"),
                ("Algorithms and Complexity", "Sorting, searching, and complexity theory (Big-O)", 5, 6, "Mandatory"),
                ("Digital Image Processing", "Image enhancement, filtering, and computer vision basics", 8, 5, "Optional"),
                ("Computer Networks I", "Network architectures, protocols, and the TCP/IP stack", 6, 6, "Mandatory"),
                ("Microprocessors", "Architecture and assembly programming of microcontrollers", 5, 7, "Mandatory"),
                ("Artificial Intelligence", "Heuristic search, logic, and machine learning principles", 7, 6, "Mandatory"),
                ("Diploma Thesis", "Year-long independent research and implementation project", 10, 30, "Mandatory")
            ]
        }
    ]
},
    {
    "name": "University of the Aegean",
    "programs": [
        {
            "type": "BSc", "title": "Marine Sciences", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Oceanography", "Overview of physical, chemical, biological, and geological oceanography", 1, 6, "Mandatory"),
                ("Marine Biology", "Study of marine organisms, their adaptations and functional biology", 3, 6, "Mandatory"),
                ("Chemical Oceanography", "Composition of seawater and biogeochemical cycles in the ocean", 4, 6, "Mandatory"),
                ("Physical Oceanography", "Ocean currents, waves, tides, and air-sea interactions", 4, 6, "Mandatory"),
                ("Marine Ecology", "Structure and function of marine ecosystems and community dynamics", 5, 6, "Mandatory"),
                ("Remote Sensing in Marine Sciences", "Satellite observation techniques for monitoring sea surface parameters", 6, 5, "Mandatory"),
                ("Marine Pollution", "Sources, fate, and impact of pollutants in the marine environment", 7, 5, "Mandatory"),
                ("Fisheries Biology", "Dynamics of exploited fish populations and sustainable management", 7, 5, "Optional"),
                ("Coastal Zone Management", "Integrated planning and legal frameworks for coastal areas", 8, 5, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Social Anthropology and History", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Introduction to Social Anthropology", "Foundations of ethnographic research and cultural theory", 1, 6, "Mandatory"),
                ("Introduction to History", "Methods of historical inquiry and schools of historiography", 1, 6, "Mandatory"),
                ("Anthropological Theory I", "Evolutionism, Functionalism, and Structuralism foundations", 2, 6, "Mandatory"),
                ("Modern Greek History", "Social and political evolution of the Greek state (19th-20th century)", 3, 6, "Mandatory"),
                ("Ethnographic Fieldwork", "Methodology and ethics of participant observation and interviewing", 5, 8, "Mandatory"),
                ("Anthropology of Gender", "Cultural constructions of masculinity, femininity, and sexuality", 4, 6, "Mandatory"),
                ("Ottoman History", "The Ottoman Empire from the conquest of Constantinople to the Tanzimat", 4, 6, "Mandatory"),
                ("Anthropology of Religion", "Ritual, symbolism, and belief systems in comparative perspective", 6, 6, "Optional"),
                ("History of the Balkans", "Ethnic conflicts and national movements in Southeastern Europe", 7, 6, "Optional")
            ]
        },
        {
            "type": "BSc", "title": "Product and Systems Design Engineering", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("Freehand Drawing", "Introduction to sketching, perspective, and visual representation", 1, 5, "Mandatory"),
                ("Introduction to Design", "Basic principles of form, function, and design thinking", 1, 6, "Mandatory"),
                ("Mathematics for Design I", "Calculus and geometry foundations for engineering and modeling", 1, 6, "Mandatory"),
                ("Computer-Aided Design (CAD I)", "Introduction to 2D and 3D digital modeling and technical drawing", 2, 6, "Mandatory"),
                ("History of Art and Design", "Evolution of visual culture and industrial design movements", 2, 5, "Mandatory"),
                ("Ergonomics", "Physical and cognitive human factors in product design", 4, 6, "Mandatory"),
                ("Human-Computer Interaction (HCI)", "User-centered design, usability testing, and interface architecture", 5, 6, "Mandatory"),
                ("Design Methodology", "Structured phases of the design process from concept to prototype", 3, 6, "Mandatory"),
                ("Interaction Design", "Design of interactive digital products and user experiences (UX)", 6, 6, "Mandatory"),
                ("Service Design", "Applying design thinking to complex systems and service delivery", 7, 6, "Mandatory"),
                ("Diploma Thesis", "Year-long comprehensive design project and documentation", 10, 30, "Mandatory")
            ]
        }
    ]
},
    {
    "name": "Democritus University of Thrace",
    "programs": [
        {
            "type": "BSc", "title": "Law", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Constitutional Law", "The fundamental organization of the State and human rights protection", 1, 7, "Mandatory"),
                ("General Principles of Civil Law", "Legal capacity, declaration of will, and the formation of contracts", 1, 8, "Mandatory"),
                ("History of Law", "Evolution of legal systems from Roman law to the modern era", 1, 5, "Mandatory"),
                ("Criminal Law (General Part)", "Theory of crime, criminal responsibility, and sentencing", 2, 7, "Mandatory"),
                ("Administrative Law", "Legal framework for public administration and administrative acts", 3, 7, "Mandatory"),
                ("International Public Law", "Legal relations between states and international organizations", 3, 6, "Mandatory"),
                ("Commercial Law (General Part)", "Regulation of merchants, commercial acts, and trademarks", 4, 6, "Mandatory"),
                ("Civil Procedure I", "The structure of courts and the stages of civil litigation", 5, 7, "Mandatory"),
                ("Labor Law", "Individual and collective labor relations and employee rights", 6, 6, "Mandatory"),
                ("Private International Law", "Conflict of laws and jurisdiction in cross-border legal issues", 7, 6, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Physical Education and Sport Science", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Human Anatomy", "Systemic study of the human body structure for physical activity", 1, 6, "Mandatory"),
                ("History of Physical Education", "Evolution of sports from antiquity to modern Olympic Games", 1, 4, "Mandatory"),
                ("Exercise Physiology I", "Acute physiological responses to physical activity and stress", 2, 6, "Mandatory"),
                ("Principles of Didactics in Sports", "Teaching methodologies for physical education in schools", 3, 5, "Mandatory"),
                ("Biomechanics", "Mechanical principles of human movement and sports performance", 3, 6, "Mandatory"),
                ("Sports Psychology", "Mental factors affecting athletic performance and motivation", 4, 5, "Mandatory"),
                ("Basketball", "Technical skills, tactics, and teaching of basketball", 2, 4, "Mandatory"),
                ("Athletics (Track & Field)", "Sprinting, jumping, and throwing techniques and coaching", 3, 4, "Mandatory"),
                ("Sports Medicine", "Prevention and rehabilitation of sports-related injuries", 6, 5, "Mandatory"),
                ("Special Physical Education", "Adaptive physical activity for people with disabilities", 7, 5, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Molecular Biology and Genetics", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("General Biology", "Cellular basis of life, organelles, and basic biological processes", 1, 6, "Mandatory"),
                ("Inorganic Chemistry", "Atomic structure, chemical bonding, and coordination compounds", 1, 6, "Mandatory"),
                ("Organic Chemistry", "Functional groups, reactions, and mechanisms in organic molecules", 2, 7, "Mandatory"),
                ("Genetics I", "Principles of Mendelian inheritance and population genetics", 2, 7, "Mandatory"),
                ("Biochemistry I", "Structure and function of proteins, enzymes, and carbohydrates", 3, 7, "Mandatory"),
                ("Molecular Biology I", "DNA replication, transcription, and translation mechanisms", 3, 7, "Mandatory"),
                ("Cell Biology", "Intracellular signaling, cell cycle, and apoptosis", 4, 7, "Mandatory"),
                ("Bioinformatics", "Computational tools for genomic sequence analysis and protein modeling", 5, 6, "Mandatory"),
                ("Biotechnology", "Recombinant DNA technology and industrial applications of microbes", 6, 6, "Mandatory"),
                ("Immunology", "Molecular basis of the immune response and antibody production", 6, 6, "Mandatory")
            ]
        }
    ]
},
    {
    "name": "University of Thessaly",
    "programs": [
        {
            "type": "BSc", "title": "Agriculture, Crop Production and Rural Environment", "lang": "Greek", "dur": "10", "ects": "300",
            "courses": [
                ("General and Inorganic Chemistry", "Principles of chemistry applied to agricultural science and plant nutrition", 1, 6, "Mandatory"),
                ("Mathematics", "Calculus and statistics for agricultural data analysis", 1, 6, "Mandatory"),
                ("General Botany", "Plant anatomy, morphology, and physiological processes", 2, 6, "Mandatory"),
                ("Soil Science", "Physical and chemical properties of soils and fertility management", 3, 6, "Mandatory"),
                ("General Entomology", "Study of insects: morphology, physiology, and ecological roles", 3, 6, "Mandatory"),
                ("Plant Pathology", "Etiology and management of plant diseases caused by fungi and bacteria", 5, 6, "Mandatory"),
                ("Pomology", "Cultivation and management of deciduous fruit trees", 7, 7, "Mandatory"),
                ("Viticulture", "Biology and cultivation techniques for grapevines", 8, 6, "Mandatory"),
                ("Plant Breeding", "Genetic improvement of crops and variety selection", 6, 6, "Mandatory"),
                ("Agrochemicals", "Use and impact of fertilizers and pesticides in crop production", 9, 5, "Mandatory"),
                ("Diploma Thesis", "Comprehensive research project on agricultural environment or production", 10, 30, "Mandatory")
            ]
        },
        {
            "type": "BSc", "title": "Biochemistry and Biotechnology", "lang": "Greek", "dur": "8", "ects": "240",
            "courses": [
                ("Cell Biology", "Molecular organization and function of eukaryotic and prokaryotic cells", 1, 6, "Mandatory"),
                ("Organic Chemistry", "Functional groups, stereochemistry, and reactions in organic synthesis", 2, 6, "Mandatory"),
                ("Biochemistry I", "Structure and function of amino acids, proteins, and enzymes", 3, 7, "Mandatory"),
                ("Molecular Biology", "Mechanisms of DNA replication, transcription, and translation", 4, 7, "Mandatory"),
                ("Enzymology", "Enzyme kinetics, mechanism of action, and industrial applications", 5, 6, "Mandatory"),
                ("Metabolic Regulation", "Pathways of carbohydrate, lipid, and nitrogen metabolism", 5, 6, "Mandatory"),
                ("Immunology", "Cellular and molecular basis of the immune response", 6, 6, "Mandatory"),
                ("Genetic Engineering", "Recombinant DNA technology and gene cloning techniques", 7, 6, "Mandatory"),
                ("Industrial Biotechnology", "Scale-up of biological processes and bioreactor design", 8, 6, "Mandatory"),
                ("Bioinformatics", "Computational analysis of genomic and proteomic data", 6, 6, "Mandatory")
            ]
        }
    ]
},
    {
        "name": "University of Ioannina",
        "programs": [
            {
                "type": "BSc", "title": "Materials Science and Engineering", "lang": "Greek", "dur": "10", "ects": "300",
                "courses": [
                    ("Physics I", "Fundamental mechanics, kinematics, and wave motion", 1, 4, "Mandatory"),
                    ("Chemistry I", "Atomic structure, chemical bonding, and stoichiometry", 1, 4, "Mandatory"),
                    ("Mathematics I", "Calculus of one variable and sequences", 1, 4, "Mandatory"),
                    ("Introduction to Materials Science", "Classification of materials and structure-property relationships", 1, 4, "Mandatory"),
                    ("Engineering Drawing", "Technical sketching and CAD foundations for engineers", 2, 4, "Mandatory"),
                    ("Linear Algebra", "Vector spaces, matrices, and linear transformations", 2, 4, "Mandatory"),
                    ("Chemical Thermodynamics", "First and second laws applied to chemical systems", 3, 4, "Mandatory"),
                    ("Continuum Mechanics", "Stress and strain analysis in continuous media", 3, 4, "Mandatory"),
                    ("Physical Metallurgy I", "Phase diagrams and properties of metallic alloys", 5, 4, "Mandatory"),
                    ("Ceramics", "Structure, processing, and properties of ceramic materials", 5, 6, "Mandatory"),
                    ("Electrical, Magnetic and Optical Properties", "Quantum mechanical foundations of material behavior", 3, 4, "Mandatory"),
                    ("Diploma Thesis", "Year-long experimental or theoretical research project", 10, 30, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Philosophy", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Introduction to Philosophy", "Major philosophical questions and historical schools", 1, 6, "Mandatory"),
                    ("Ancient Greek Philosophy I", "Pre-Socratic thinkers and the Sophists", 1, 6, "Mandatory"),
                    ("Logic I", "Propositional logic and foundations of reasoning", 2, 6, "Mandatory"),
                    ("Modern Philosophy", "Rationalism and Empiricism from Descartes to Kant", 3, 6, "Mandatory"),
                    ("Social and Political Philosophy", "Theories of the state, justice, and individual rights", 4, 6, "Mandatory"),
                    ("Epistemology", "The nature of knowledge, truth, and justification", 5, 6, "Mandatory"),
                    ("Ethics", "Normative theories and meta-ethics foundations", 6, 6, "Mandatory"),
                    ("Philosophy of Science", "Methods and logic of scientific discovery and theory", 6, 6, "Mandatory"),
                    ("Contemporary Philosophy", "Phenomenology, Existentialism, and Analytic traditions", 7, 6, "Mandatory")
                ]
            }
        ]
    },
    {
        "name": "Ionian University",
        "programs": [
            {
                "type": "BSc", "title": "Foreign Languages, Translation and Interpreting", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Translation Theory and Practice I", "Foundational concepts and strategies in translation", 1, 6, "Mandatory"),
                    ("English Language and Language Analysis", "Advanced linguistics and syntax of the English language", 1, 6, "Mandatory"),
                    ("Modern Greek Language I", "Style, grammar, and composition for translators", 1, 6, "Mandatory"),
                    ("Translation English-Greek I", "General text translation and terminology management", 2, 7, "Mandatory"),
                    ("History of European Literature", "Key movements and authors in the Western tradition", 2, 5, "Mandatory"),
                    ("Economic and Legal Translation", "Specialized translation of financial and judicial documents", 5, 6, "Mandatory"),
                    ("Introduction to Interpreting", "Consecutive interpreting techniques and note-taking", 5, 6, "Mandatory"),
                    ("Technical and Scientific Translation", "Handling complex industrial and medical terminology", 6, 6, "Mandatory"),
                    ("Simultaneous Interpreting", "Booth practice and real-time oral translation", 7, 8, "Optional"),
                    ("Dissertation", "Research project on translation studies or interpreting", 8, 12, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Archives, Library Science and Museology", "lang": "Greek", "dur": "8", "ects": "255",
                "courses": [
                    ("Introduction to Archival Science", "Principles of appraisal, arrangement, and description", 1, 5, "Mandatory"),
                    ("Introduction to Museology", "Theory and history of museums and collections", 1, 4, "Mandatory"),
                    ("Informatics", "Computer systems for information management", 1, 5, "Mandatory"),
                    ("Greek Palaeography", "Study of ancient and medieval Greek handwriting", 1, 4, "Mandatory"),
                    ("History of the Modern Greek State", "Institutional evolution of Greece (1821-present)", 2, 4, "Mandatory"),
                    ("Book and Printing History", "From the invention of the press to the digital era", 2, 4, "Mandatory"),
                    ("Databases", "Relational design for information professionals", 3, 5, "Mandatory"),
                    ("Cataloguing and Encoding in MARC", "Standardized bibliographic description for libraries", 3, 5, "Mandatory"),
                    ("Digital Libraries", "Architecture and management of electronic collections", 5, 5, "Mandatory"),
                    ("Metadata Standards for Museums", "Documenting intangible and material culture", 6, 5, "Mandatory")
                ]
            }
        ]
    },
    {
        "name": "Panteion University",
        "programs": [
            {
                "type": "BSc", "title": "Political Science and History", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Introduction to Political Science", "Key concepts, power structures, and political systems", 1, 6, "Mandatory"),
                    ("History of the Modern Greek State", "Political and social evolution of Greece since 1821", 1, 6, "Mandatory"),
                    ("Introduction to International Relations", "Theories of global politics and international actors", 2, 6, "Mandatory"),
                    ("Political Sociology", "The relationship between society, class, and political power", 3, 6, "Mandatory"),
                    ("Modern European History", "Major European transformations from the French Revolution to WWII", 2, 6, "Mandatory"),
                    ("Political Theory", "Analysis of political thought from Machiavelli to Marx", 4, 6, "Mandatory"),
                    ("Public Policy", "The process of policy making, implementation, and evaluation", 5, 5, "Mandatory"),
                    ("Comparative Politics", "Comparing democratic and authoritarian regimes globally", 6, 5, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Sociology", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("History of Sociological Theory I", "Foundations of sociology: Comte, Marx, Durkheim, Weber", 1, 6, "Mandatory"),
                    ("Methodology of Social Research", "Quantitative and qualitative research design and ethics", 2, 6, "Mandatory"),
                    ("Social Stratification", "Inequality, social mobility, and class structures", 3, 6, "Mandatory"),
                    ("Urban Sociology", "Social dynamics of city life, housing, and urban development", 4, 6, "Mandatory"),
                    ("Sociology of the Family", "Evolution of family structures and kinship in modern society", 5, 5, "Mandatory"),
                    ("Criminology", "Theories of deviance, crime, and social control", 6, 5, "Mandatory"),
                    ("Sociology of Labor", "Changes in the workplace, unions, and the global economy", 5, 5, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Communication, Media and Culture", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Introduction to Communication", "Theoretical models of human and mass communication", 1, 6, "Mandatory"),
                    ("History of Media", "Evolution of the press, radio, television, and the internet", 2, 6, "Mandatory"),
                    ("Cultural Management", "Managing art, heritage, and creative industries", 3, 6, "Mandatory"),
                    ("Digital Journalism", "Content creation and ethics in the age of social media", 4, 6, "Mandatory"),
                    ("Semiotics", "Analysis of signs, symbols, and meaning in media texts", 5, 5, "Mandatory"),
                    ("Psychology of Media", "Mass influence, perception, and audience behavior", 6, 5, "Mandatory"),
                    ("Public Relations", "Strategic communication and corporate image management", 5, 5, "Mandatory")
                ]
            }
        ]
    },
    {
        "name": "Harokopio University",
        "programs": [
            {
                "type": "BSc", "title": "Nutrition and Dietetics", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Human Physiology", "Systemic study of the human body and vital functions", 1, 6, "Mandatory"),
                    ("General and Inorganic Chemistry", "Chemical principles for health sciences", 1, 5, "Mandatory"),
                    ("Biochemistry of Metabolism", "Nutrient processing and metabolic pathways in the human body", 3, 6, "Mandatory"),
                    ("Food Chemistry", "Chemical composition and transformations of food materials", 4, 6, "Mandatory"),
                    ("Clinical Nutrition I", "Dietary management of obesity, diabetes, and cardiovascular diseases", 5, 7, "Mandatory"),
                    ("Medical Nutrition Therapy II", "Advanced nutrition support for renal and hepatic conditions", 6, 7, "Mandatory"),
                    ("Community Nutrition", "Public health programs and nutrition policy", 4, 5, "Mandatory"),
                    ("Food Microbiology", "Microorganisms in food production and safety", 3, 5, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Geography", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Introduction to Geography", "Main themes of physical and human geography", 1, 5, "Mandatory"),
                    ("Physical Geography", "Natural processes of the earth: climate, water, and soil", 1, 6, "Mandatory"),
                    ("Cartography", "Principles of map design, scales, and projections", 2, 6, "Mandatory"),
                    ("Geographic Information Systems (GIS)", "Spatial data analysis and mapping using software", 3, 7, "Mandatory"),
                    ("Economic Geography", "Spatial organization of economic activities and trade", 4, 6, "Mandatory"),
                    ("Geomorphology", "Study of landforms and the processes that shape them", 3, 6, "Mandatory"),
                    ("Urban Geography", "Global urbanization trends and city planning", 5, 6, "Mandatory"),
                    ("Remote Sensing", "Analyzing earth data from satellite and aerial imagery", 6, 7, "Mandatory")
                ]
            }
        ]
    },
   {
        "name": "University of West Attica",
        "programs": [
            {
                "type": "BSc", "title": "Biomedical Engineering", "lang": "Greek", "dur": "10", "ects": "300",
                "courses": [
                    ("Biomedical Technology", "Introduction to medical devices and clinical engineering standards", 1, 5, "Mandatory"),
                    ("Medical Imaging Systems I", "Physics and engineering of X-rays, CT scans, and Ultrasound", 7, 6, "Mandatory"),
                    ("Biomaterials", "Properties of materials for implants and tissue engineering", 6, 5, "Mandatory"),
                    ("Biological Signal Processing", "Analysis of EEG, ECG, and EMG signals using MATLAB", 5, 6, "Mandatory"),
                    ("Human Physiology for Engineers", "Functional analysis of the human body from a systems perspective", 2, 5, "Mandatory"),
                    ("Biomechanics", "Kinematics and dynamics of human movement and prosthetic design", 4, 6, "Mandatory"),
                    ("Medical Robotics", "Automation and robotics in surgery and rehabilitation", 8, 5, "Mandatory"),
                    ("Clinical Engineering", "Management and safety of medical technology in hospital environments", 9, 5, "Mandatory"),
                    ("Diploma Thesis", "Year-long research project in biomedical innovation", 10, 30, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Graphic Design and Visual Communication", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Typography I", "The history and anatomy of type and page layout foundations", 1, 6, "Mandatory"),
                    ("Color Theory", "Physics and psychology of color in visual communication", 1, 4, "Mandatory"),
                    ("History of Art", "Evolution of visual arts from prehistory to the Renaissance", 1, 4, "Mandatory"),
                    ("Packaging Design", "Structural and graphic design for consumer products", 5, 6, "Mandatory"),
                    ("Branding and Identity", "Creating visual identities, logos, and brand guidelines", 6, 6, "Mandatory"),
                    ("Web Design", "User interface (UI) and user experience (UX) for digital platforms", 4, 6, "Mandatory"),
                    ("Illustration", "Traditional and digital techniques for narrative visualization", 3, 5, "Mandatory"),
                    ("Motion Graphics", "Time-based design, animation, and video editing for communication", 7, 6, "Mandatory")
                ]
            }
        ]
    },
    {
        "name": "University of the Peloponnese",
        "programs": [
            {
                "type": "BSc", "title": "Informatics and Telecommunications", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Structured Programming", "Fundamentals of algorithms and programming using C", 1, 7, "Mandatory"),
                    ("Digital Design", "Logic circuits, Boolean algebra, and hardware foundations", 1, 6, "Mandatory"),
                    ("Object-Oriented Programming", "Software development principles using Java", 2, 7, "Mandatory"),
                    ("Data Structures", "Analysis of lists, stacks, trees, and searching algorithms", 3, 7, "Mandatory"),
                    ("Operating Systems", "Process management, memory, and file systems", 4, 6, "Mandatory"),
                    ("Database Systems", "Relational modeling and SQL language", 4, 6, "Mandatory"),
                    ("Computer Networks", "Architecture and protocols of the Internet stack", 5, 6, "Mandatory"),
                    ("Wireless Communications", "Signal propagation and mobile network technologies", 7, 6, "Mandatory"),
                    ("Artificial Intelligence", "Knowledge representation and machine learning basics", 6, 6, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Nursing", "lang": "Greek", "dur": "8", "ects": "240",
                "courses": [
                    ("Anatomy I", "Descriptive study of the human musculoskeletal and nervous system", 1, 6, "Mandatory"),
                    ("Basic Nursing I", "Foundational skills and ethics in patient care", 1, 7, "Mandatory"),
                    ("Physiology I", "Biological functions of human cells and organ systems", 1, 6, "Mandatory"),
                    ("Internal Medicine Nursing I", "Care for patients with acute and chronic medical conditions", 3, 7, "Mandatory"),
                    ("Surgical Nursing I", "Perioperative care and operating room protocols", 4, 7, "Mandatory"),
                    ("Pharmacology", "Drug administration, interactions, and nursing responsibilities", 2, 5, "Mandatory"),
                    ("Pediatric Nursing", "Care of infants, children, and adolescents", 5, 6, "Mandatory"),
                    ("Psychiatric Nursing", "Mental health assessment and therapeutic interventions", 6, 6, "Mandatory"),
                    ("Community Nursing", "Public health and home-based patient care", 7, 6, "Mandatory")
                ]
            }
        ]
    },
   {
        "name": "Hellenic Mediterranean University",
        "programs": [
            {
                "type": "BSc", "title": "Agriculture", "lang": "Greek", "dur": "10", "ects": "300",
                "courses": [
                    ("Introduction to Agronomy", "Basic principles of scientific agriculture and crop classification", 1, 5, "Mandatory"),
                    ("Plant Anatomy and Morphology", "Microscopic and macroscopic structure of higher plants", 1, 6, "Mandatory"),
                    ("General and Inorganic Chemistry", "Principles of chemistry for agricultural applications", 1, 5, "Mandatory"),
                    ("Soil Science", "Chemical and physical properties of soil and fertility management", 3, 5, "Mandatory"),
                    ("Genetics", "Mendelian inheritance and molecular genetics in plants", 3, 5, "Mandatory"),
                    ("Plant Physiology", "Metabolic processes, photosynthesis, and plant growth regulators", 4, 5, "Mandatory"),
                    ("Field Crop Production I", "Cultivation of cereals and legumes for food and feed", 5, 5, "Mandatory"),
                    ("Entomology", "Biology and control of insects affecting agricultural production", 6, 5, "Mandatory"),
                    ("Food Microbiology", "Microbiological safety and processing of agricultural products", 7, 5, "Mandatory"),
                    ("Diseases of Fruit Trees and Grapevine", "Diagnosis and management of fungal and viral infections", 6, 5, "Mandatory"),
                    ("Apiculture", "Biology of the honeybee and modern beekeeping techniques", 8, 5, "Optional"),
                    ("Diploma Thesis", "Final year research project in agricultural sciences", 10, 30, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Electrical and Computer Engineering", "lang": "Greek", "dur": "10", "ects": "300",
                "courses": [
                    ("Structured Programming", "Problem-solving and C programming for engineers", 1, 5, "Mandatory"),
                    ("Linear Algebra and Calculus", "Vector spaces, matrices, and integral calculus", 1, 5, "Mandatory"),
                    ("Physics for Engineers", "Mechanics and thermodynamics foundations", 1, 5, "Mandatory"),
                    ("Electric Circuit Lectures", "DC/AC analysis, Ohm's law, and network theorems", 1, 5, "Mandatory"),
                    ("Digital Systems", "Combinational and sequential logic circuit design", 2, 5, "Mandatory"),
                    ("Data Structures", "Analysis and implementation of lists, trees, and graphs", 3, 6, "Mandatory"),
                    ("Microprocessors", "Architecture, instruction sets, and assembly programming", 5, 6, "Mandatory"),
                    ("Operating Systems", "Process management, memory, and parallel systems", 6, 6, "Mandatory"),
                    ("Power Systems – Steady State Analysis", "Modeling of generators, lines, and load flow analysis", 7, 4, "Mandatory"),
                    ("Embedded Systems", "Hardware-software co-design for specialized computing", 8, 6, "Mandatory"),
                    ("Multimedia Technologies", "Processing of digital audio, image, and video data", 9, 4, "Optional")
                ]
            }
        ]
    },
    {
        "name": "International Hellenic University",
        "programs": [
            {
                "type": "MSc", "title": "Strategic Product Design", "lang": "English", "dur": "3", "ects": "90",
                "courses": [
                    ("Introduction to Strategic Product Design", "Evolution of design paradigms and user-centered innovation", 1, 6, "Mandatory"),
                    ("New Product Development", "Lifecycle of products from ideation to commercialization", 1, 6, "Mandatory"),
                    ("Marketing Analysis and Brand Research", "Consumer behavior and strategic brand positioning", 1, 6, "Mandatory"),
                    ("3D Computer Aided Design (Rhinoceros)", "Advanced 3D modeling and surface design techniques", 2, 6, "Mandatory"),
                    ("Design Thinking", "Human-centric problem solving and creative methodology", 2, 6, "Mandatory"),
                    ("Reverse Engineering and 3D Printing", "Digitizing physical objects and additive manufacturing", 2, 3, "Optional"),
                    ("Automation and Robotics", "Integration of robotic systems in industrial design", 2, 3, "Optional"),
                    ("Sustainable Product Design", "Ecological considerations and circular economy in design", 2, 3, "Optional"),
                    ("Master's Dissertation", "Independent research or design project", 3, 30, "Mandatory")
                ]
            },
            {
                "type": "BSc", "title": "Informatics Engineering", "lang": "Greek", "dur": "10", "ects": "300",
                "courses": [
                    ("Mathematics I", "Calculus and analytical geometry foundations", 1, 5, "Mandatory"),
                    ("Computer Programming I", "Introduction to procedural programming with Python/C", 1, 5, "Mandatory"),
                    ("Physics II", "Electricity and magnetism for computer engineers", 2, 5, "Mandatory"),
                    ("Operating Systems I", "Introduction to OS kernels and shell scripting", 2, 5, "Mandatory"),
                    ("Electric Circuits", "Foundations of electronic circuits and components", 2, 5, "Mandatory"),
                    ("Software Engineering", "Development lifecycles, UML, and project management", 7, 5, "Mandatory"),
                    ("Mobile Applications Development", "Programming for iOS and Android platforms", 8, 6, "Mandatory"),
                    ("Internet of Things (IoT)", "Smart city solutions and interconnected embedded devices", 7, 6, "Mandatory"),
                    ("Big Data and Cloud Computing", "Distributed storage, Spark, and cloud architectures", 9, 6, "Mandatory"),
                    ("Advanced Digital Systems", "FPGA design and hardware description languages", 6, 5, "Optional")
                ]
            }
        ]
    }
]

skills_data = [
    {"skill_name": "Python (computer programming)", "skill_url": "http://data.europa.eu/esco/skill/5c92000c-0b04-4f0f-9afb-0fbc5e9c5a0f", "esco_id": "5c92000c-0b04-4f0f-9afb-0fbc5e9c5a0f", "esco_level": "ESCO"},
    {"skill_name": "C programming language", "skill_url": "http://data.europa.eu/esco/skill/7d4b6a79-97c4-4a8d-b08a-75d8e9e6fcd7", "esco_id": "7d4b6a79-97c4-4a8d-b08a-75d8e9e6fcd7", "esco_level": "ESCO"},
    {"skill_name": "C++", "skill_url": "http://data.europa.eu/esco/skill/46141443-39d6-444f-8314-8742880775a8", "esco_id": "46141443-39d6-444f-8314-8742880775a8", "esco_level": "ESCO"},
    {"skill_name": "Java (computer programming)", "skill_url": "http://data.europa.eu/esco/skill/ba55f4aa-9f0b-4e2d-8d0b-8f5b0e3c9b90", "esco_id": "ba55f4aa-9f0b-4e2d-8d0b-8f5b0e3c9b90", "esco_level": "ESCO"},
    {"skill_name": "SQL", "skill_url": "http://data.europa.eu/esco/skill/38ac41e7-b57c-4225-96ad-1e178b018b63", "esco_id": "38ac41e7-b57c-4225-96ad-1e178b018b63", "esco_level": "ESCO"},
    {"skill_name": "Object-oriented programming", "skill_url": "http://data.europa.eu/esco/skill/e191f5b1-4149-4afb-a61c-e414ba31b6dc", "esco_id": "e191f5b1-4149-4afb-a61c-e414ba31b6dc", "esco_level": "ESCO"},
    {"skill_name": "Data structures", "skill_url": "http://data.europa.eu/esco/skill/6f6f2b7f-2f44-4a35-bc38-47c7a6d2a8fd", "esco_id": "6f6f2b7f-2f44-4a35-bc38-47c7a6d2a8fd", "esco_level": "ESCO"},
    {"skill_name": "Algorithms", "skill_url": "http://data.europa.eu/esco/skill/90f8d9a1-7c3c-4f50-bb0e-1bbcc9c4bfa4", "esco_id": "90f8d9a1-7c3c-4f50-bb0e-1bbcc9c4bfa4", "esco_level": "ESCO"},
    {"skill_name": "Operating systems", "skill_url": "http://data.europa.eu/esco/skill/6d5d9c8a-0d6b-4b5e-9b5c-2f17c0e6df3e", "esco_id": "6d5d9c8a-0d6b-4b5e-9b5c-2f17c0e6df3e", "esco_level": "ESCO"},
    {"skill_name": "Computer networks", "skill_url": "http://data.europa.eu/esco/skill/1e9fbdab-b9b1-4d4d-b8f1-ff2c6df9b12a", "esco_id": "1e9fbdab-b9b1-4d4d-b8f1-ff2c6df9b12a", "esco_level": "ESCO"},
    {"skill_name": "Database management systems", "skill_url": "http://data.europa.eu/esco/skill/45b09fa2-4c73-4b80-b1b4-4ba5ffcd8791", "esco_id": "45b09fa2-4c73-4b80-b1b4-4ba5ffcd8791", "esco_level": "ESCO"},
    {"skill_name": "Cybersecurity", "skill_url": "http://data.europa.eu/esco/skill/3413f53a-b7f1-4a1c-9bb1-b931fae1f616", "esco_id": "3413f53a-b7f1-4a1c-9bb1-b931fae1f616", "esco_level": "ESCO"},
    {"skill_name": "Cloud computing", "skill_url": "http://data.europa.eu/esco/skill/0ec5728a-773a-4467-96a9-839e5576a084", "esco_id": "0ec5728a-773a-4467-96a9-839e5576a084", "esco_level": "ESCO"},
    {"skill_name": "Distributed systems", "skill_url": "http://data.europa.eu/esco/skill/3c2df3b0-0f0f-4d92-9c73-8bda58c4b4f5", "esco_id": "3c2df3b0-0f0f-4d92-9c73-8bda58c4b4f5", "esco_level": "ESCO"},
    {"skill_name": "Embedded systems", "skill_url": "http://data.europa.eu/esco/skill/4a7c5b4a-70b6-4f88-9c6a-0a5f5b32f5a1", "esco_id": "4a7c5b4a-70b6-4f88-9c6a-0a5f5b32f5a1", "esco_level": "ESCO"},
    {"skill_name": "Machine learning", "skill_url": "http://data.europa.eu/esco/skill/48f06947-f404-4340-96f8-4e144a1e9411", "esco_id": "48f06947-f404-4340-96f8-4e144a1e9411", "esco_level": "ESCO"},
    {"skill_name": "Deep learning", "skill_url": "http://data.europa.eu/esco/skill/7aa1a5bd-f7fc-4c52-93f0-edcec6a2ef49", "esco_id": "7aa1a5bd-f7fc-4c52-93f0-edcec6a2ef49", "esco_level": "ESCO"},
    {"skill_name": "Neural networks", "skill_url": "http://data.europa.eu/esco/skill/0f58b4d2-71d1-4d65-b47c-cc0a68c3e0b2", "esco_id": "0f58b4d2-71d1-4d65-b47c-cc0a68c3e0b2", "esco_level": "ESCO"},
    {"skill_name": "Data mining", "skill_url": "http://data.europa.eu/esco/skill/9b1b3b0b-6c1a-4b6e-9c72-1f8a6c8d4f2e", "esco_id": "9b1b3b0b-6c1a-4b6e-9c72-1f8a6c8d4f2e", "esco_level": "ESCO"},
    {"skill_name": "Statistical analysis", "skill_url": "http://data.europa.eu/esco/skill/09f5d0e5-5275-4f14-9edb-b36e71350941", "esco_id": "09f5d0e5-5275-4f14-9edb-b36e71350941", "esco_level": "ESCO"},
    {"skill_name": "Data visualisation", "skill_url": "http://data.europa.eu/esco/skill/0a41596b-7201-4c7a-b4af-698786a6e7d3", "esco_id": "0a41596b-7201-4c7a-b4af-698786a6e7d3", "esco_level": "ESCO"},
    {"skill_name": "Natural language processing", "skill_url": "http://data.europa.eu/esco/skill/8a5f1db7-8a63-4c42-b5d7-47c87f7e6d12", "esco_id": "8a5f1db7-8a63-4c42-b5d7-47c87f7e6d12", "esco_level": "ESCO"},
    {"skill_name": "Computer vision", "skill_url": "http://data.europa.eu/esco/skill/2f9e8a3c-6d45-4e0c-8f5c-3a1b6d7e4c92", "esco_id": "2f9e8a3c-6d45-4e0c-8f5c-3a1b6d7e4c92", "esco_level": "ESCO"},
    {"skill_name": "Big data analytics", "skill_url": "http://data.europa.eu/esco/skill/1f0e8d77-7b9c-4c63-9d1c-bb5e3f6c9b4a", "esco_id": "1f0e8d77-7b9c-4c63-9d1c-bb5e3f6c9b4a", "esco_level": "ESCO"},
    {"skill_name": "Recommender systems", "skill_url": "http://data.europa.eu/esco/skill/3c7d8b1e-9f3a-4e5c-8a9d-1b6e5f4c3d2a", "esco_id": "3c7d8b1e-9f3a-4e5c-8a9d-1b6e5f4c3d2a", "esco_level": "ESCO"},
    {"skill_name": "Linear algebra", "skill_url": "http://data.europa.eu/esco/skill/54c8c0a6-2b7e-4e4f-9b0b-3f6b1a9e5c7d", "esco_id": "54c8c0a6-2b7e-4e4f-9b0b-3f6b1a9e5c7d", "esco_level": "ESCO"},
    {"skill_name": "Calculus", "skill_url": "http://data.europa.eu/esco/skill/9d6e3c5b-4a2f-4b8d-8c7a-1f6b5d3e9c2a", "esco_id": "9d6e3c5b-4a2f-4b8d-8c7a-1f6b5d3e9c2a", "esco_level": "ESCO"},
    {"skill_name": "Structural analysis", "skill_url": "http://data.europa.eu/esco/skill/6064f58c-d07a-4934-bc2c-745a7b054817", "esco_id": "6064f58c-d07a-4934-bc2c-745a7b054817", "esco_level": "ESCO"},
    {"skill_name": "Thermodynamics", "skill_url": "http://data.europa.eu/esco/skill/474d221c-8433-4613-a4f6-599f57c9c049", "esco_id": "474d221c-8433-4613-a4f6-599f57c9c049", "esco_level": "ESCO"},
    {"skill_name": "Fluid mechanics", "skill_url": "http://data.europa.eu/esco/skill/1a9fe8ce-da00-457a-9fb2-644265f64d6c", "esco_id": "1a9fe8ce-da00-457a-9fb2-644265f64d6c", "esco_level": "ESCO"},
    {"skill_name": "Control systems", "skill_url": "http://data.europa.eu/esco/skill/930c198f-6cd9-438b-9ad6-37e6cbe82601", "esco_id": "930c198f-6cd9-438b-9ad6-37e6cbe82601", "esco_level": "ESCO"},
    {"skill_name": "Electrical circuits", "skill_url": "http://data.europa.eu/esco/skill/4d0b9c5a-7f3b-4e6d-8a9c-2f6b5d4e3c1a", "esco_id": "4d0b9c5a-7f3b-4e6d-8a9c-2f6b5d4e3c1a", "esco_level": "ESCO"},
    {"skill_name": "Microprocessors", "skill_url": "http://data.europa.eu/esco/skill/0d8f6c7b-9a5e-4b3d-8c1f-2e6b5d4c3a9", "esco_id": "0d8f6c7b-9a5e-4b3d-8c1f-2e6b5d4c3a9", "esco_level": "ESCO"},
    {"skill_name": "Robotics", "skill_url": "http://data.europa.eu/esco/skill/0b7a8c9d-6f5e-4a3b-8c2d-1e6b5d4c3f9a", "esco_id": "0b7a8c9d-6f5e-4a3b-8c2d-1e6b5d4c3f9a", "esco_level": "ESCO"},
    {"skill_name": "Computer-aided design", "skill_url": "http://data.europa.eu/esco/skill/7f425890-7613-433e-b873-1d0e515e0655", "esco_id": "7f425890-7613-433e-b873-1d0e515e0655", "esco_level": "ESCO"},
    {"skill_name": "Human anatomy", "skill_url": "http://data.europa.eu/esco/skill/5a6d3c9b-4f8e-4b7c-9a1e-2f6b5d4c3a8e", "esco_id": "5a6d3c9b-4f8e-4b7c-9a1e-2f6b5d4c3a8e", "esco_level": "ESCO"},
    {"skill_name": "Physiology", "skill_url": "http://data.europa.eu/esco/skill/8c6b5d4e-3f2a-4c9b-8a7d-1e6b5d4c3a9", "esco_id": "8c6b5d4e-3f2a-4c9b-8a7d-1e6b5d4c3a9", "esco_level": "ESCO"},
    {"skill_name": "Medical diagnosis", "skill_url": "http://data.europa.eu/esco/skill/519f727c-3f2b-45e0-8451-8409e563604f", "esco_id": "519f727c-3f2b-45e0-8451-8409e563604f", "esco_level": "ESCO"},
    {"skill_name": "Nursing care", "skill_url": "http://data.europa.eu/esco/skill/f19f727c-3f2b-45e0-8451-8409e563604f", "esco_id": "f19f727c-3f2b-45e0-8451-8409e563604f", "esco_level": "ESCO"},
    {"skill_name": "Pharmacology", "skill_url": "http://data.europa.eu/esco/skill/8f773956-628d-4254-9407-7429188d4076", "esco_id": "8f773956-628d-4254-9407-7429188d4076", "esco_level": "ESCO"},
    {"skill_name": "Legal research", "skill_url": "http://data.europa.eu/esco/skill/93273841-3e5e-498c-986c-85196f7e8492", "esco_id": "93273841-3e5e-498c-986c-85196f7e8492", "esco_level": "ESCO"},
    {"skill_name": "International law", "skill_url": "http://data.europa.eu/esco/skill/1d5b6c9a-8f3e-4b7c-9a2e-2f6b5d4c3a1e", "esco_id": "1d5b6c9a-8f3e-4b7c-9a2e-2f6b5d4c3a1e", "esco_level": "ESCO"},
    {"skill_name": "Econometrics", "skill_url": "http://data.europa.eu/esco/skill/83273841-3e5e-498c-986c-85196f7e8492", "esco_id": "83273841-3e5e-498c-986c-85196f7e8492", "esco_level": "ESCO"},
    {"skill_name": "Financial accounting", "skill_url": "http://data.europa.eu/esco/skill/d0c2a846-bb50-4c70-9f2d-89e9445cd24b", "esco_id": "d0c2a846-bb50-4c70-9f2d-89e9445cd24b", "esco_level": "ESCO"},
    {"skill_name": "Project management", "skill_url": "http://data.europa.eu/esco/skill/55d5c5c6-0c95-41c0-91a3-f883ff6d36e4", "esco_id": "55d5c5c6-0c95-41c0-91a3-f883ff6d36e4", "esco_level": "ESCO"},
]


occupations_data = [
    {"occupation_id": "2512.1", "occupation_name": "Software Developer", "occupation_url": "http://data.europa.eu/esco/occupation/2512.1", "esco_code": "2512.1"},
    {"occupation_id": "2511.2", "occupation_name": "Data Scientist", "occupation_url": "http://data.europa.eu/esco/occupation/2511.2", "esco_code": "2511.2"},
    {"occupation_id": "2529.1", "occupation_name": "Cybersecurity Specialist", "occupation_url": "http://data.europa.eu/esco/occupation/2529.1", "esco_code": "2529.1"},
    {"occupation_id": "2142.1", "occupation_name": "Civil Engineer", "occupation_url": "http://data.europa.eu/esco/occupation/2142.1", "esco_code": "2142.1"},
    {"occupation_id": "2144.1", "occupation_name": "Mechanical Engineer", "occupation_url": "http://data.europa.eu/esco/occupation/2144.1", "esco_code": "2144.1"},
    {"occupation_id": "2145.1", "occupation_name": "Chemical Engineer", "occupation_url": "http://data.europa.eu/esco/occupation/2145.1", "esco_code": "2145.1"},
    {"occupation_id": "2149.5", "occupation_name": "Biomedical Engineer", "occupation_url": "http://data.europa.eu/esco/occupation/2149.5", "esco_code": "2149.5"},
    {"occupation_id": "2211.1", "occupation_name": "Generalist Medical Practitioner", "occupation_url": "http://data.europa.eu/esco/occupation/2211.1", "esco_code": "2211.1"},
    {"occupation_id": "2221.1", "occupation_name": "Nursing Professional", "occupation_url": "http://data.europa.eu/esco/occupation/2221.1", "esco_code": "2221.1"},
    {"occupation_id": "2265.1", "occupation_name": "Dietitian", "occupation_url": "http://data.europa.eu/esco/occupation/2265.1", "esco_code": "2265.1"},
    {"occupation_id": "2251.1", "occupation_name": "Veterinarian", "occupation_url": "http://data.europa.eu/esco/occupation/2251.1", "esco_code": "2251.1"},
    {"occupation_id": "2422.1", "occupation_name": "Policy Adviser", "occupation_url": "http://data.europa.eu/esco/occupation/2422.1", "esco_code": "2422.1"},
    {"occupation_id": "2611.1", "occupation_name": "Lawyer", "occupation_url": "http://data.europa.eu/esco/occupation/2611.1", "esco_code": "2611.1"},
    {"occupation_id": "2411.1", "occupation_name": "Accountant / Auditor", "occupation_url": "http://data.europa.eu/esco/occupation/2411.1", "esco_code": "2411.1"},
    {"occupation_id": "1324.4", "occupation_name": "Shipping Manager", "occupation_url": "http://data.europa.eu/esco/occupation/1324.4", "esco_code": "1324.4"},
    {"occupation_id": "2163.2", "occupation_name": "Product Designer", "occupation_url": "http://data.europa.eu/esco/occupation/2163.2", "esco_code": "2163.2"},
    {"occupation_id": "2643.1", "occupation_name": "Translator", "occupation_url": "http://data.europa.eu/esco/occupation/2643.1", "esco_code": "2643.1"},
    {"occupation_id": "2632.1", "occupation_name": "Sociologist / Social Researcher", "occupation_url": "http://data.europa.eu/esco/occupation/2632.1", "esco_code": "2632.1"},
]
skill_occupation_links = [
    ("Python (computer programming)", "2511.2"),        
    ("Machine learning", "2511.2"),
    ("Deep learning", "2511.2"),
    ("Data mining", "2511.2"),
    ("Big data analytics", "2511.2"),
    ("Statistical analysis", "2511.2"),
    ("Python (computer programming)", "2512.1"),       
    ("Object-oriented programming", "2512.1"),
    ("Algorithms", "2512.1"),
    ("Data structures", "2512.1"),
    ("Database management systems", "2512.1"),
    ("Computer networks", "2512.1"),
    ("Cybersecurity", "2529.1"),                       
    ("Network security", "2529.1"),
    ("Structural analysis", "2142.1"),                
    ("CAD", "2142.1"),
    ("Fluid mechanics", "2142.1"),
    ("Thermodynamics", "2144.1"),                      
    ("Control systems", "2144.1"),
    ("Microprocessors", "2144.1"),
    ("Chemical engineering", "2145.1"),               
    ("Process engineering", "2145.1"),
    ("Robotics", "2149.5"),                           
    ("Medical imaging", "2149.5"),
    ("Medical diagnosis", "2211.1"),                   
    ("Human anatomy", "2211.1"),
    ("Physiology", "2211.1"),
    ("Nursing care", "2221.1"),                        
    ("Patient care", "2221.1"),
    ("Clinical nutrition", "2265.1"),                   
    ("Legal research", "2611.1"),                      
    ("International law", "2611.1"),
    ("Public policy analysis", "2422.1"),              
    ("Translation", "2643.1"),                          
    ("UX/UI Design", "2163.2"),                        
    ("Interaction design", "2163.2"),
]

SKILL_KEYWORDS = {
    "Python (computer programming)": ["python"],
    "C programming language": ["c programming", "c language"],
    "C++": ["c++"],
    "Java (computer programming)": ["java"],
    "SQL": ["sql", "database", "query"],
    "Object-oriented programming": ["oop", "object oriented", "class", "inheritance"],
    "Data structures": ["data structures", "stack", "queue", "tree", "graph"],
    "Algorithms": ["algorithm", "complexity", "sorting", "searching"],
    "Operating systems": ["operating system", "kernel", "process", "thread"],
    "Computer networks": ["network", "tcp", "ip", "protocol"],
    "Database management systems": ["database", "dbms", "sql"],
    "Cybersecurity": ["security", "cybersecurity", "encryption"],
    "Cloud computing": ["cloud", "distributed", "virtualisation"],
    "Distributed systems": ["distributed", "consensus", "scalability"],
    "Embedded systems": ["embedded", "microcontroller"],
    "Machine learning": ["machine learning", "ml"],
    "Deep learning": ["deep learning", "neural network"],
    "Neural networks": ["neural", "cnn", "rnn"],
    "Data mining": ["data mining", "clustering"],
    "Big data analytics": ["big data", "spark", "hadoop"],
    "Statistical analysis": ["statistics", "regression", "probability"],
    "Natural language processing": ["nlp", "language processing"],
    "Computer vision": ["computer vision", "image processing"],
    "Recommender systems": ["recommender", "collaborative filtering"],
    "Data visualisation": ["visualisation", "charts", "graphs"],
    "Linear algebra": ["linear algebra", "matrix", "vector"],
    "Calculus": ["calculus", "derivative", "integral"],
    "Structural analysis": ["structural", "mechanics"],
    "Thermodynamics": ["thermodynamics", "heat", "energy"],
    "Fluid mechanics": ["fluid", "hydraulics"],
    "Control systems": ["control", "pid", "feedback"],
    "Electrical circuits": ["circuit", "voltage", "current"],
    "Microprocessors": ["microprocessor", "assembly"],
    "Robotics": ["robotics", "automation"],
    "Computer-aided design": ["cad", "design software"],
    "Human anatomy": ["anatomy"],
    "Physiology": ["physiology"],
    "Medical diagnosis": ["diagnosis", "clinical"],
    "Nursing care": ["nursing", "patient care"],
    "Pharmacology": ["pharmacology", "drug"],
    "Medical imaging": ["imaging", "radiology"],
    "Clinical nutrition": ["nutrition", "diet"],
    "Legal research": ["legal research", "law"],
    "International law": ["international law"],
    "Public policy analysis": ["public policy", "policy analysis"],
    "Ethnographic research": ["ethnography", "anthropology"],
    "Econometrics": ["econometrics", "regression"],
    "Financial accounting": ["accounting", "financial statements"],
    "Financial auditing": ["audit", "auditing"],
    "Risk management": ["risk", "risk management"],
    "Project management": ["project management", "planning"],
    "Translation": ["translation", "interpreting"],
    "Technical writing": ["technical writing"],
    "UX/UI Design": ["ux", "ui", "user experience"],
    "Interaction design": ["interaction", "interface"],
}

def backfill_course_sections(db: Session):
    from sqlalchemy import select

    def is_missing(value):
        return value is None or not value.strip()

    courses = db.execute(select(Course)).scalars().all()
    fixed = 0

    for course in courses:
        needs_fix = (
            is_missing(course.objectives)
            or is_missing(course.learning_outcomes)
            or is_missing(course.course_content)
        )

        if not needs_fix:
            continue

        generated = generate_course_sections(
            course.lesson_name,
            course.description or ""
        )

        if is_missing(course.objectives):
            course.objectives = generated["objectives"]

        if is_missing(course.learning_outcomes):
            course.learning_outcomes = generated["learning_outcomes"]

        if is_missing(course.course_content):
            course.course_content = generated["course_content"]

        fixed += 1

    print(f"🛠️ Auto-filled course sections for {fixed} courses")




def generate_course_sections(course_name: str, description: str):
    name = course_name.lower()
    desc = (description or "").strip()



    if any(k in name for k in ["atomic", "quantum", "physics", "mechanics", "electromagnetism"]):
        return {
            "objectives": (
                "To develop a solid understanding of fundamental physical principles "
                "governing matter, energy, and their interactions at classical and quantum levels."
            ),
            "learning_outcomes": (
                "Upon successful completion of the course, students will be able to:\n"
                "- Explain core physical laws and models\n"
                "- Apply mathematical tools to physical systems\n"
                "- Analyze experimental and theoretical physical phenomena"
            ),
            "course_content": (
                desc if desc else
                "Classical and modern physics concepts, analytical models, "
                "problem-solving techniques, and real-world applications."
            )
        }
        
    if any(k in name for k in [
    "probability", "statistics", "statistical", "stochastic",
    "random", "random variables", "distribution"
    ]):
        return {
            "objectives": (
                "To introduce the mathematical foundations of probability and statistics, "
                "enabling students to model uncertainty and analyze random phenomena."
            ),
            "learning_outcomes": (
                "After completing this course, students will be able to:\n"
                "- Define and manipulate probability spaces\n"
                "- Analyze random variables and probability distributions\n"
                "- Apply probabilistic reasoning to real-world problems"
            ),
            "course_content": (
                desc if desc else
                "Probability axioms, random variables, discrete and continuous distributions, "
                "expectation, variance, and introductory statistical inference."
            )
        }


    if any(k in name for k in [
        "programming", "algorithm", "data", "computer", "software",
        "database", "operating", "network", "ai", "machine learning",
        "artificial intelligence", "distributed", "cloud"
    ]):
        return {
            "objectives": (
                "To equip students with theoretical foundations and practical skills "
                "in computing, algorithmic thinking, and software system design."
            ),
            "learning_outcomes": (
                "After completing this course, students will be able to:\n"
                "- Design and implement computational solutions\n"
                "- Analyze algorithmic efficiency and system behavior\n"
                "- Apply programming and data-handling techniques to real problems"
            ),
            "course_content": (
                desc if desc else
                "Programming concepts, data structures, algorithms, system architectures, "
                "and applied computing methodologies."
            )
        }

    if any(k in name for k in [
        "engineering", "circuits", "control", "thermodynamics", "fluid",
        "mechanics", "structures", "materials", "electronics", "signals"
    ]):
        return {
            "objectives": (
                "To provide engineering students with analytical tools and applied knowledge "
                "for modeling, designing, and optimizing technical systems."
            ),
            "learning_outcomes": (
                "Students completing this course will be able to:\n"
                "- Apply engineering principles to solve real-world problems\n"
                "- Analyze system behavior using mathematical models\n"
                "- Design and evaluate engineering components and processes"
            ),
            "course_content": (
                desc if desc else
                "Engineering theory, mathematical modeling, laboratory applications, "
                "and system-level analysis."
            )
        }

    if any(k in name for k in [
        "medical", "anatomy", "physiology", "nursing",
        "pharmacology", "diagnosis", "clinical", "biochemistry"
    ]):
        return {
            "objectives": (
                "To develop scientific and clinical knowledge essential for understanding "
                "human health, disease mechanisms, and patient care."
            ),
            "learning_outcomes": (
                "Upon completion, students will be able to:\n"
                "- Describe normal and pathological biological processes\n"
                "- Apply clinical reasoning and diagnostic principles\n"
                "- Integrate scientific knowledge into healthcare practice"
            ),
            "course_content": (
                desc if desc else
                "Human anatomy and physiology, disease mechanisms, diagnostic methods, "
                "therapeutic principles, and clinical applications."
            )
        }

    if any(k in name for k in [
        "law", "legal", "constitutional", "criminal", "civil",
        "international", "administrative", "maritime"
    ]):
        return {
            "objectives": (
                "To introduce students to fundamental legal principles, legal reasoning, "
                "and the structure of legal systems at national and international levels."
            ),
            "learning_outcomes": (
                "After completing the course, students will be able to:\n"
                "- Interpret and apply legal rules and concepts\n"
                "- Analyze legal cases and statutory frameworks\n"
                "- Develop structured legal arguments"
            ),
            "course_content": (
                desc if desc else
                "Legal sources, doctrines, case law analysis, and application of law "
                "to practical and theoretical problems."
            )
        }

    if any(k in name for k in [
        "economics", "finance", "accounting", "management",
        "marketing", "business", "auditing", "econometrics"
    ]):
        return {
            "objectives": (
                "To provide analytical tools and conceptual frameworks for understanding "
                "economic behavior, markets, and organizational decision-making."
            ),
            "learning_outcomes": (
                "Students will be able to:\n"
                "- Analyze economic and financial data\n"
                "- Apply economic models to real-world scenarios\n"
                "- Make informed managerial and policy decisions"
            ),
            "course_content": (
                desc if desc else
                "Economic theory, quantitative methods, financial analysis, "
                "and business strategy applications."
            )
        }


    if any(k in name for k in [
        "history", "sociology", "anthropology", "political",
        "psychology", "philosophy", "education", "communication"
    ]):
        return {
            "objectives": (
                "To cultivate critical thinking and analytical skills for understanding "
                "social structures, cultural processes, and human behavior."
            ),
            "learning_outcomes": (
                "After completing this course, students will be able to:\n"
                "- Apply theoretical perspectives to social phenomena\n"
                "- Critically analyze historical and social data\n"
                "- Conduct basic qualitative and quantitative research"
            ),
            "course_content": (
                desc if desc else
                "Theoretical approaches, empirical research methods, "
                "case studies, and critical analysis of social issues."
            )
        }

    if any(k in name for k in [
        "design", "architecture", "art", "visual",
        "ux", "ui", "media", "communication"
    ]):
        return {
            "objectives": (
                "To develop creative, technical, and conceptual skills for the design "
                "and evaluation of visual, spatial, and interactive systems."
            ),
            "learning_outcomes": (
                "Students completing this course will be able to:\n"
                "- Apply design principles and methodologies\n"
                "- Create and evaluate visual or spatial artifacts\n"
                "- Integrate aesthetics with functionality and user needs"
            ),
            "course_content": (
                desc if desc else
                "Design theory, visual communication, project-based work, "
                "and critique-driven development."
            )
        }
        
    if any(k in name for k in ["shipping", "maritime", "port", "logistics"]):
        return {
            "objectives": (
                "To examine the organizational, operational, and strategic management "
                "of shipping companies within the global maritime industry."
            ),
            "learning_outcomes": (
                "Students will be able to:\n"
                "- Understand shipping company structures\n"
                "- Analyze maritime business strategies\n"
                "- Evaluate operational and regulatory challenges in shipping"
            ),
            "course_content": (
                desc if desc else
                "Shipping markets, maritime economics, fleet management, "
                "chartering strategies, and regulatory frameworks."
            )
        }


    return {
        "objectives": (
            f"To provide students with a solid theoretical and practical understanding of {course_name}."
        ),
        "learning_outcomes": (
            "After completing this course, students will be able to:\n"
            f"- Understand key concepts related to {course_name}\n"
            "- Apply theoretical knowledge to practical problems\n"
            "- Analyze and synthesize information in the subject area"
        ),
        "course_content": (
            desc if desc else f"Core topics and methodologies related to {course_name}."
        )
    }



def run_seed():
    init_db()
    db: Session = SessionLocal()

    try:
        courses_by_name = {}

        for uni in GREEK_UNI_DATA:
            university = get_or_create(
                db,
                University,
                {"university_name": uni["name"], "country": "Greece"}
            )

            for p in uni["programs"]:
                program = get_or_create(
                    db,
                    DegreeProgram,
                    {
                        "university_id": university.university_id,
                        "degree_type": p["type"],
                        "language": p["lang"],
                        "degree_titles": [p["title"]],
                    },
                    {
                        "duration_semesters": p["dur"],
                        "total_ects": p["ects"],
                    }
                )

                for name, desc, sem, ects, mand in p["courses"]:
                    sections = generate_course_sections(name, desc)
                    course = get_or_create(
                        db,
                        Course,
                        {
                            "lesson_name": name,
                            "program_id": program.program_id,
                        },
                        {
                            "university_id": university.university_id,
                            "description": desc,
                            "objectives": sections["objectives"],
                            "learning_outcomes": sections["learning_outcomes"],
                            "course_content": sections["course_content"],
                            "language": p["lang"],
                            "semester_number": str(sem),
                            "ects_list": [ects],
                            "mand_opt_list": [mand],
                            "msc_bsc_list": [p["type"]],
                        }
                    )
                    key = (name, program.program_id)
                    courses_by_name.setdefault(key, []).append(course)

                    
        backfill_course_sections(db)

        skills = {}
        for s in skills_data:
            skill = get_or_create(
                db,
                Skill,
                {"skill_name": s["skill_name"], "skill_url": s["skill_url"]},
                {
                    "esco_id": s["esco_id"],
                    "esco_level": s["esco_level"],
                }
            )
            skills[s["skill_name"]] = skill

  
        for skill_name, skill in skills.items():
            keywords = SKILL_KEYWORDS.get(skill_name, [])
            if not keywords:
                continue

            for course_list in courses_by_name.values():
                for course in course_list:
                    text = f"{course.lesson_name} {course.description}".lower()
                    if any(k in text for k in keywords):
                        exists = db.execute(
                            select(CourseSkill).where(
                                CourseSkill.course_id == course.course_id,
                                CourseSkill.skill_id == skill.skill_id
                            )
                        ).scalar_one_or_none()

                        if not exists:
                            db.add(
                                CourseSkill(
                                    course_id=course.course_id,
                                    skill_id=skill.skill_id,
                                    categories=["auto"]
                                )
                            )



        occupations = {}
        for o in occupations_data:
            occ = get_or_create(
                db,
                Occupation,
                {"occupation_id": o["occupation_id"]},
                {
                    "occupation_name": o["occupation_name"],
                    "occupation_url": o["occupation_url"],
                    "esco_code": o["esco_code"],
                }
            )
            occupations[o["occupation_id"]] = occ

        for skill_name, occ_id in skill_occupation_links:
            def norm(s): return s.lower().strip()

            skills = {norm(k): v for k, v in skills.items()}

            skill = skills.get(norm(skill_name))

            occ = occupations.get(occ_id)
            if not skill or not occ:
                continue

            exists = db.execute(
                select(SkillOccupation).where(
                    SkillOccupation.skill_id == skill.skill_id,
                    SkillOccupation.occupation_id == occ.occupation_id,
                )
            ).scalar_one_or_none()

            if not exists:
                db.add(
                    SkillOccupation(
                        skill_id=skill.skill_id,
                        occupation_id=occ.occupation_id
                    )
                )

        db.commit()
        print("✅ Greek seed FULLY completed.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise

    finally:
        db.close()

if __name__ == "__main__":
    run_seed()