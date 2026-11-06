"""Complete 100-lesson AI syllabus (Basics -> Advanced) + weekend fun facts.
Each lesson carries verified CORE FACTS. The script writer must stay faithful to them and a second AI fact-checks against them."""
from util import log

# (title in Hinglish, title in English, core facts, Indian everyday analogy, keywords)
_BASICS = [
 ("AI kya hai?", "What is AI?", "AI means machines doing tasks that normally need human intelligence, like recognising speech or images, translating and making decisions. Today's AI is narrow: very good at specific tasks, not general human-like thinking.", "phone ka voice assistant, maps, face unlock", ["AI", "narrow AI", "machine"]),
 ("AI vs ML vs Deep Learning", "AI vs ML vs Deep Learning", "AI is the big umbrella. Machine Learning is a part of AI where systems learn from data. Deep Learning is a part of ML that uses neural networks with many layers.", "dabba ke andar dabba (Russian dolls)", ["AI", "ML", "deep learning"]),
 ("Machine Learning kaise kaam karta hai?", "How Machine Learning works", "Instead of writing rules by hand, we give the algorithm many examples (data). It finds patterns and produces a model that can predict on new data.", "chai wala jo aapka order yaad rakhta hai", ["data", "pattern", "model", "prediction"]),
 ("Data kya hai aur kyun zaroori hai?", "What is data and why it matters", "Data is recorded examples such as numbers, text, images or clicks. The quality and quantity of data strongly limit how good a model can be: garbage in, garbage out.", "recipe ke ingredients", ["data", "dataset", "quality"]),
 ("Algorithm ka simple matlab", "Algorithm explained", "An algorithm is a step-by-step procedure to solve a problem. In ML, the learning algorithm is the procedure that adjusts a model using data.", "cooking recipe ke steps", ["algorithm", "steps"]),
 ("Model kya hota hai?", "What is a model", "A model is the result of training: a mathematical function with learned numbers called parameters that turns inputs into outputs.", "exam ke baad bana hua notes ka formula", ["model", "parameters"]),
 ("Training vs Testing", "Training vs Testing", "Data is split into a training set, used to learn, and a test set the model has never seen, used to check how well it generalises. Testing on training data gives an over-optimistic score.", "practice match vs real match", ["train", "test", "generalise"]),
 ("Supervised Learning", "Supervised Learning", "Supervised learning learns from labelled examples, meaning inputs paired with correct answers. Examples: spam vs not spam, house price prediction.", "teacher ke paas answer key", ["labels", "supervised"]),
 ("Unsupervised Learning", "Unsupervised Learning", "Unsupervised learning finds structure in data that has no labels, for example grouping similar customers into clusters.", "bina label ke kapde alag-alag dher mein sort karna", ["clustering", "unlabelled"]),
 ("Reinforcement Learning", "Reinforcement Learning", "In reinforcement learning an agent learns by trial and error, getting rewards or penalties for its actions. It is used in game playing and robotics.", "video game jahan points milte hain", ["agent", "reward", "environment"]),
 ("Classification vs Regression", "Classification vs Regression", "Classification predicts a category such as spam or not spam. Regression predicts a number such as price or temperature.", "haan/naa vs kitna?", ["classification", "regression"]),
 ("Features aur Labels", "Features and Labels", "Features are the input variables that describe each example. The label is the target value we want the model to predict.", "student ki profile vs result", ["features", "label"]),
 ("Overfitting kya hai?", "Overfitting", "Overfitting happens when a model memorises training data, including noise, and performs poorly on new data.", "exam ke liye ratta maarna", ["overfitting", "memorise"]),
 ("Underfitting kya hai?", "Underfitting", "Underfitting happens when a model is too simple to capture the pattern, so it performs poorly on both training and new data.", "sirf chapter ke headings padhna", ["underfitting", "simple model"]),
 ("Bias aur Variance", "Bias and Variance", "High bias means the model is too simple and underfits. High variance means it is too sensitive to the training data and overfits. Good models balance both.", "tir-andazi mein nishana", ["bias", "variance"]),
 ("Neural Network kya hai?", "What is a Neural Network", "A neural network is layers of simple connected units called neurons. Each neuron multiplies inputs by weights, adds a bias, applies an activation function and passes the result on. It is only loosely inspired by the brain.", "office mein message ek se doosre ko pass hona", ["neuron", "layers", "weights"]),
 ("Weights aur Bias", "Weights and Bias", "Weights decide how important each input is. Bias shifts the output. Training adjusts weights and biases to reduce error.", "exam mein marks ka weightage", ["weights", "bias"]),
 ("Activation Function", "Activation Function", "An activation function such as ReLU or sigmoid adds non-linearity so a network can learn complex patterns. Without it, many layers would collapse into one linear function.", "switch jo decide kare signal aage jaye ya nahi", ["ReLU", "sigmoid", "non-linear"]),
 ("Loss Function", "Loss Function", "A loss function is a number that measures how wrong the predictions are. Training tries to make the loss as small as possible.", "dart bullseye se kitna door hai", ["loss", "error"]),
 ("Gradient Descent", "Gradient Descent", "Gradient descent repeatedly adjusts parameters in the direction that reduces the loss, using the gradient. The step size is the learning rate.", "kohre mein pahaad se neeche utarna", ["gradient", "learning rate"]),
 ("Learning Rate", "Learning Rate", "The learning rate controls the step size in gradient descent. Too high can overshoot or diverge, too low makes training very slow.", "seedhi utarte waqt kadam ka size", ["learning rate", "step"]),
 ("Epoch aur Batch", "Epoch and Batch", "An epoch is one full pass through the training data. Data is usually processed in small groups called batches, with one parameter update per batch.", "syllabus ke revision rounds", ["epoch", "batch"]),
 ("Computer Vision", "Computer Vision", "Computer vision teaches machines to understand images and video. Common tasks are image classification, object detection and segmentation.", "aap apne dost ka chehra kaise pehchante ho", ["vision", "detection"]),
 ("NLP: Language samajhna", "Natural Language Processing", "Natural Language Processing lets machines work with human language: translation, sentiment analysis, chatbots and summarising.", "Google Translate aur autocorrect", ["NLP", "text"]),
 ("Speech Recognition", "Speech Recognition", "Speech recognition converts spoken audio into text. Text-to-speech does the reverse. Both power voice assistants and voice typing.", "WhatsApp voice typing", ["speech", "audio"]),
 ("Recommendation System", "Recommendation Systems", "Recommendation systems predict what a user may like using their own past behaviour and the behaviour of similar users. Streaming and shopping apps use them.", "kirana wala uncle jo aapki pasand jaanta hai", ["recommendation", "similar users"]),
 ("Generative AI kya hai?", "What is Generative AI", "Generative AI models create new content such as text, images, audio or code by learning patterns from large amounts of data, instead of only classifying existing data.", "bahut kitabein padh ke apne words mein essay likhna", ["generative", "content"]),
 ("AI galat bhi ho sakta hai", "AI can be wrong", "AI systems can be wrong, biased or confidently incorrect, so important outputs should always be verified by a person.", "GPS kabhi galat mod bata deta hai", ["errors", "verify"]),
 ("AI Bias kya hota hai?", "AI Bias", "If training data is unbalanced or reflects unfairness, a model can give unfair results. Diverse data and testing across groups help reduce bias.", "ek hi taraf ki baat sunne wala teacher", ["bias", "fairness", "data"]),
 ("AI aur Privacy", "AI and Privacy", "Responsible AI means respecting privacy, consent and transparency. Avoid sharing sensitive personal data such as passwords or ID numbers with online AI tools.", "diary pe lock", ["privacy", "ethics"]),
]
_INTER = [
 ("Python AI ke liye kyun?", "Why Python for AI", "Python is the most popular language for AI because of libraries like NumPy, pandas, scikit-learn, PyTorch and TensorFlow, and because it is easy to read.", "Swiss army knife", ["Python", "libraries"]),
 ("NumPy aur Arrays", "NumPy and arrays", "NumPy provides fast multi-dimensional arrays and vectorised maths. It is the foundation of most ML libraries in Python.", "calculator jo poori list ek saath calculate kare", ["NumPy", "array"]),
 ("pandas aur DataFrame", "pandas and DataFrames", "pandas gives table-like DataFrames to load, clean, filter and group data from files such as CSV.", "Excel sheet lekin code mein", ["pandas", "DataFrame"]),
 ("Data Cleaning", "Data Cleaning", "Before training we handle missing values, duplicates, outliers and wrong data types. Clean data usually improves results more than fancy models.", "chawal mein se kankad chunna", ["missing values", "outliers"]),
 ("Train, Validation, Test split", "Train/Validation/Test split", "Training data is for learning, validation data is for tuning settings, and the test set is used only once at the end for an honest final score.", "practice, mock test, final exam", ["validation", "test"]),
 ("Cross-Validation", "Cross-Validation", "In k-fold cross-validation, data is split into k parts. The model is trained and validated k times, each time holding out a different part, and the scores are averaged.", "alag alag chapters se mock test", ["k-fold", "validation"]),
 ("Accuracy kab dhoka deti hai?", "Accuracy and its trap", "Accuracy is the fraction of correct predictions. On imbalanced data it can mislead: a model that always says 'not fraud' can be 99% accurate and still useless.", "99 saal ka mareez ghar mein, sab healthy bol do", ["accuracy", "imbalanced"]),
 ("Precision aur Recall", "Precision and Recall", "Precision is the share of predicted positives that were truly positive. Recall is the share of actual positives that were found.", "machhli pakadne ka jaal", ["precision", "recall"]),
 ("F1 Score aur Confusion Matrix", "F1 score and Confusion Matrix", "A confusion matrix counts true positives, false positives, false negatives and true negatives. F1 is the harmonic mean of precision and recall.", "report card ka breakdown", ["F1", "confusion matrix"]),
 ("Linear Regression", "Linear Regression", "Linear regression fits a straight line y = w*x + b to data by minimising squared error, to predict a number.", "area se ghar ki keemat ka andaza", ["line", "regression"]),
 ("Logistic Regression", "Logistic Regression", "Despite its name, logistic regression is a classification method. It outputs a probability using the sigmoid function.", "pass hone ka chance percent mein", ["sigmoid", "probability"]),
 ("Decision Tree", "Decision Trees", "A decision tree asks a series of if/else questions to split data until it reaches a prediction. It is easy to interpret but can overfit.", "20 questions game", ["tree", "split"]),
 ("Random Forest", "Random Forest", "A random forest trains many decision trees on random subsets of data and features, then averages or votes. This reduces overfitting.", "doston ki committee se vote", ["ensemble", "forest"]),
 ("k-Nearest Neighbours", "k-Nearest Neighbours", "kNN classifies a new point by looking at the k closest training examples and taking a majority vote.", "aapke padosi kaise hain, aap bhi waise", ["kNN", "distance"]),
 ("Support Vector Machine", "Support Vector Machine", "An SVM finds the decision boundary that separates classes with the widest possible margin.", "do gaon ke beech sabse chaudi sadak", ["SVM", "margin"]),
 ("K-Means Clustering", "K-Means Clustering", "K-Means groups data into k clusters by assigning each point to the nearest centre and then moving the centres, repeating until stable.", "shaadi mein tables par mehmaan baithana", ["cluster", "centroid"]),
 ("Dimensionality Reduction aur PCA", "PCA", "PCA reduces the number of features while keeping as much variation in the data as possible.", "3D object ki 2D photo", ["PCA", "features"]),
 ("Feature Engineering", "Feature Engineering", "Creating better input features from raw data, such as extracting day of week from a date, often improves a model more than changing the algorithm.", "kachche aam se achaar banana", ["features", "engineering"]),
 ("Normalization aur Scaling", "Scaling features", "Scaling puts features on similar ranges so training is stable and no feature dominates just because its numbers are larger.", "sab marks ko 100 mein convert karna", ["scaling", "normalise"]),
 ("Hyperparameters", "Hyperparameters", "Hyperparameters are settings chosen before training, such as learning rate or tree depth. Parameters are the values learned during training.", "oven ka temperature vs bana hua cake", ["hyperparameter", "tuning"]),
 ("Regularization", "Regularization", "Regularization techniques such as L1, L2 and dropout discourage overly complex models, which reduces overfitting.", "bahut zyada decoration se bachna", ["L2", "dropout"]),
 ("Backpropagation", "Backpropagation", "Backpropagation computes how much each weight contributed to the error by applying the chain rule backwards through the network. Gradient descent then updates the weights.", "galti ka zimmedar kaun, peeche se dhoondhna", ["backprop", "gradient"]),
 ("Deep Learning", "Deep Learning", "Deep learning uses neural networks with many layers. Early layers learn simple features and later layers learn more complex ones. It needs lots of data and compute.", "multi-floor building", ["deep", "layers"]),
 ("CNN: Image samajhne wala network", "Convolutional Neural Networks", "A CNN slides small filters over an image to detect edges, then shapes, then objects. It shares weights across positions, which makes it efficient for images.", "torch se andhere kamre ko scan karna", ["CNN", "filters"]),
 ("RNN aur LSTM", "RNN and LSTM", "Recurrent networks process sequences step by step while carrying a memory. LSTMs handle longer dependencies. Transformers have replaced them for many language tasks.", "kahani sunte waqt pichla scene yaad rakhna", ["RNN", "LSTM", "sequence"]),
 ("Transfer Learning", "Transfer Learning", "Transfer learning reuses a model pretrained on a large dataset and adapts it to a new task, needing much less data and time.", "cricketer ka tennis seekhna", ["pretrained", "fine-tune"]),
 ("Embeddings", "Embeddings", "An embedding represents a word, image or item as a list of numbers (a vector) so that similar things are close together.", "map par shehron ki jagah", ["embedding", "vector"]),
 ("Tokenization", "Tokenization", "Text is split into tokens, which are words or pieces of words, and each token is mapped to a number before a language model processes it.", "vakya ko shabdon mein todna", ["token", "subword"]),
 ("Cosine Similarity", "Vector similarity", "Cosine similarity compares the direction of two embedding vectors. Higher means more similar meaning. It powers semantic search.", "do logon ki pasand kitni milti hai", ["cosine", "semantic search"]),
 ("Attention ka intuition", "Attention intuition", "Attention lets a model weigh which parts of the input matter most for each part of the output.", "padhte waqt important line ko highlight karna", ["attention", "focus"]),
 ("Transformer kya hai?", "Transformers", "The Transformer architecture was introduced in the 2017 paper Attention Is All You Need. It relies on self-attention and processes tokens in parallel. It is the basis of modern large language models.", "poori class ek saath baat kare, line mein nahi", ["transformer", "self-attention"]),
 ("LLM kya hota hai?", "What is an LLM", "A Large Language Model is a transformer trained on huge amounts of text to predict the next token. Its abilities come from scale and training data.", "autocomplete ka bahut bada bhai", ["LLM", "next token"]),
 ("LLM kaise train hota hai?", "How LLMs are trained", "LLMs are first pretrained on large text by predicting the next token. Then they are tuned to follow instructions, often using human feedback.", "pehle padhai, phir interview ki practice", ["pretraining", "instruction tuning"]),
 ("Prompt Engineering basics", "Prompt Engineering", "Clear instructions, relevant context, examples and a requested output format help an LLM give better answers.", "restaurant mein saaf order dena", ["prompt", "context"]),
 ("Zero-shot aur Few-shot", "Zero-shot and Few-shot", "Zero-shot means asking without examples. Few-shot means putting a few examples in the prompt to show the desired pattern.", "bina example vs example dikha ke samjhana", ["few-shot", "examples"]),
 ("Hallucination", "Hallucination", "LLMs can produce fluent but false statements because they predict plausible text rather than checking facts. Important answers should be verified.", "confident dost jo guess ko fact bata de", ["hallucination", "verify"]),
 ("Context Window", "Context Window", "The context window is the maximum number of tokens a model can consider at once, covering both the prompt and the generated answer.", "table jitni badi utni files rakh sakte ho", ["context", "tokens"]),
 ("Temperature aur Sampling", "Temperature", "Temperature controls randomness when picking the next token. Low temperature gives predictable output, high temperature gives more varied output.", "safe order vs kuch naya try karna", ["temperature", "sampling"]),
 ("RAG kya hai?", "Retrieval-Augmented Generation", "RAG first retrieves relevant documents and gives them to the LLM, so answers are grounded in your own data and can cite sources.", "open book exam", ["RAG", "retrieval"]),
 ("Vector Database", "Vector Databases", "A vector database stores embeddings and quickly finds the nearest ones, enabling semantic search and RAG.", "library mein topic se milti kitaabein dhoondhna", ["vector DB", "nearest neighbour"]),
]
_ADV = [
 ("Fine-tuning vs Prompting", "Fine-tuning vs Prompting", "Fine-tuning updates a model's weights using your data. Prompting and RAG change the input without changing the weights.", "naya course join karna vs notes dekh ke jawab dena", ["fine-tune", "prompt"]),
 ("LoRA: Sasta Fine-tuning", "LoRA", "LoRA fine-tunes a model by training small added matrices instead of all weights, which greatly cuts memory and cost.", "poori kitab badalne ke bajaye sticky notes", ["LoRA", "PEFT"]),
 ("Quantization", "Quantization", "Quantization stores model weights with fewer bits, such as 8-bit or 4-bit, to save memory and speed up inference with a small quality loss.", "HD photo ko compress karna", ["quantization", "bits"]),
 ("Training vs Inference cost", "Training vs Inference", "Training is a large one-time cost to learn weights. Inference is the cost of using the trained model, and it grows with the number of users.", "factory banana vs roz production", ["training", "inference"]),
 ("GPU AI ke liye kyun?", "Why GPUs for AI", "GPUs have thousands of cores that do many matrix operations in parallel, which is exactly what neural networks need.", "ek cashier vs 1000 cashier", ["GPU", "parallel"]),
 ("Scaling Laws", "Scaling Laws", "Research found that model performance tends to improve predictably as data, compute and parameters grow, though with diminishing returns.", "jitna practice utna better, par ek had tak", ["scaling", "compute"]),
 ("Self-Attention: Q, K, V", "Self-attention with Q, K, V", "Each token makes a query, key and value vector. Attention weights come from softmax of query-key dot products scaled by root of dimension, and are used to mix the values.", "library search: sawaal, index, kitab", ["query", "key", "value"]),
 ("Positional Encoding", "Positional Encoding", "Self-attention alone ignores word order, so transformers add positional information to the token embeddings.", "line mein khade logon ke number", ["position", "order"]),
 ("Encoder vs Decoder models", "Encoder vs Decoder", "Encoder models like BERT are good at understanding text. Decoder models like GPT generate text token by token. Encoder-decoder models suit translation.", "padhne wala vs likhne wala", ["encoder", "decoder"]),
 ("Mixture of Experts", "Mixture of Experts", "In a mixture-of-experts model, a router sends each token to a few expert sub-networks, so only part of the model is active per token.", "hospital mein sahi specialist ke paas bhejna", ["MoE", "router"]),
 ("RLHF", "RLHF", "In RLHF, humans rank model outputs, a reward model learns those preferences, and the language model is optimised to produce outputs the reward model scores higher.", "judges ke marks se performance sudharna", ["RLHF", "reward"]),
 ("Diffusion Models", "Diffusion Models", "Diffusion models learn to remove noise step by step. To generate an image they start from random noise and denoise it, guided by a text prompt.", "dhundhli photo ko dheere dheere saaf karna", ["diffusion", "noise"]),
 ("GANs", "GANs", "A GAN has a generator that creates samples and a discriminator that tries to tell real from fake. They improve by competing.", "nakli note banane wala vs pakadne wala", ["GAN", "generator"]),
 ("Autoencoders", "Autoencoders", "An autoencoder compresses input into a small code and then reconstructs it, learning useful compact representations.", "zip file banana aur kholna", ["autoencoder", "compression"]),
 ("AI Agents", "AI Agents", "An AI agent combines an LLM with tools in a loop: plan, take an action, observe the result and repeat until the goal is done.", "personal assistant jo kaam khatam karke batata hai", ["agent", "tools", "loop"]),
 ("Tool Use / Function Calling", "Function calling", "With function calling, an LLM outputs a structured request for an external function or API, and the program runs it and returns the result.", "waiter order kitchen tak pahunchata hai", ["function calling", "API"]),
 ("Multimodal AI", "Multimodal models", "Multimodal models can handle more than one kind of data, such as text, images and audio, in the same system.", "dekhna, sunna aur padhna ek saath", ["multimodal", "image", "audio"]),
 ("LLM Evaluation", "Evaluating LLMs", "LLMs are evaluated with benchmarks, human review and sometimes another model as judge. Benchmarks can leak into training data, so scores need care.", "board exam vs real life skill", ["benchmark", "eval"]),
 ("Guardrails aur AI Safety", "Guardrails and AI Safety", "Guardrails such as input and output filters, policies and red-teaming help keep AI systems from producing harmful outputs.", "road par speed breakers", ["safety", "red-teaming"]),
 ("Alignment", "Alignment", "Alignment is about making AI systems act in line with human intentions and values, including when instructions are ambiguous.", "peon ko sahi matlab samjhana", ["alignment", "values"]),
 ("Explainable AI", "Explainable AI", "Explainability methods such as SHAP and LIME show which input features influenced a particular prediction.", "result ke saath marking scheme", ["SHAP", "LIME"]),
 ("MLOps", "MLOps", "MLOps is the practice of deploying, monitoring and retraining models reliably, like DevOps for machine learning.", "restaurant kitchen ka roz ka system", ["deploy", "monitor"]),
 ("Data Drift", "Data Drift", "Data drift happens when real-world data changes compared to training data, which can slowly reduce model accuracy.", "purane map se naye shehar mein navigate", ["drift", "monitoring"]),
 ("A/B Testing for models", "A/B testing", "A/B testing compares two versions of a model or feature on live traffic to see which performs better.", "do alag chai recipes ko customers se chakhwana", ["A/B", "experiment"]),
 ("Knowledge Distillation", "Knowledge Distillation", "In distillation, a small student model is trained to imitate a large teacher model, keeping much of the quality at lower cost.", "topper ke notes se padhna", ["distillation", "student"]),
 ("Federated Learning", "Federated Learning", "Federated learning trains a shared model across many devices while the raw data stays on each device.", "sab apne ghar mein padh ke sirf notes bhejte hain", ["federated", "privacy"]),
 ("Edge AI", "Edge AI", "Edge AI runs models directly on phones or devices, which can reduce delay and keep data private.", "ghar ka mixer vs bahar ki juice shop", ["edge", "on-device"]),
 ("AI mein career kaise shuru karein", "How to start a career in AI", "A practical path is: learn Python, basic maths and statistics, core machine learning, then build and publish small projects.", "gym plan: roz thoda practice", ["roadmap", "projects"]),
 ("3 Projects jo aapko banane chahiye", "Three beginner AI projects", "Good beginner projects are a spam classifier, an image classifier and a small RAG chatbot over your own documents, each shared with code.", "resume ke liye portfolio", ["projects", "portfolio"]),
 ("Aage ka Rasta: Recap", "Recap and learning path", "AI changes fast, so strong fundamentals matter most. Keep practising, verify claims, and keep learning step by step.", "ek ek seedhi chadhna", ["recap", "fundamentals"]),
]

def _build():
    lessons, n = [], 0
    for level, rows in (("basics", _BASICS), ("intermediate", _INTER), ("advanced", _ADV)):
        for t, te, facts, analogy, kw in rows:
            n += 1
            lessons.append({"id": n, "level": level, "title": t, "title_en": te, "facts": facts,
                            "analogy": analogy, "keywords": kw,
                            "difficulty": {"basics": "beginner", "intermediate": "intermediate", "advanced": "advanced"}[level]})
    return lessons

LESSONS = _build()
TOTAL = len(LESSONS)

FUN_FACTS = [
 ("AI shabd kab bana?", "The term 'artificial intelligence' was coined for a summer workshop at Dartmouth College in 1956, which is considered the birth of AI as a field."),
 ("Turing ka sawaal", "In 1950 Alan Turing proposed the imitation game, now called the Turing test, asking whether a machine can be told apart from a human in conversation."),
 ("Pehla chatbot ELIZA", "ELIZA, built by Joseph Weizenbaum in 1966, was a simple pattern-matching chatbot, yet many users felt it understood them."),
 ("Deep Blue vs Kasparov", "In 1997 IBM's Deep Blue defeated world chess champion Garry Kasparov in a match."),
 ("AlphaGo ki jeet", "In March 2016 DeepMind's AlphaGo beat Go champion Lee Sedol 4 games to 1."),
 ("Perceptron", "Frank Rosenblatt introduced the perceptron in 1958, an early learning machine that was a forerunner of neural networks."),
 ("ImageNet moment", "In 2012 the deep neural network AlexNet won the ImageNet image recognition competition by a large margin, which sparked the deep learning boom."),
 ("Transformer ka paper", "The Transformer architecture came from the 2017 research paper titled Attention Is All You Need."),
 ("GPT ka matlab", "GPT stands for Generative Pre-trained Transformer."),
 ("reCAPTCHA ka kaam", "Early reCAPTCHA puzzles helped digitise scanned books by asking people to type words that computers could not read."),
 ("Netflix Prize", "From 2006 to 2009 Netflix ran a contest offering one million dollars to whoever could best improve its movie recommendation algorithm."),
 ("AlphaFold aur Nobel", "AlphaFold predicts protein structures from their sequences. In 2024 the Nobel Prize in Chemistry was shared by Demis Hassabis and John Jumper of DeepMind and David Baker."),
 ("AI winter", "AI has had 'winters', periods such as the 1970s and late 1980s when funding and interest dropped because progress fell short of promises."),
 ("Robot shabd", "The word robot comes from the 1920 Czech play R.U.R. by Karel Capek, derived from the Czech word robota meaning forced labour."),
 ("Phone ka autocomplete", "The next-word suggestions on a phone keyboard come from a small language model trained to predict what you will type next."),
 ("Spam filter", "Early email spam filters often used a simple method called Naive Bayes, which is a machine learning classifier."),
 ("Google Translate ka badlav", "In 2016 Google Translate began switching to neural machine translation, which made translations more fluent."),
 ("DALL-E ka naam", "OpenAI said the name DALL-E is a mix of the artist Salvador Dali and Pixar's robot WALL-E."),
 ("Python ka naam", "The Python programming language is named after the comedy group Monty Python, not the snake."),
 ("GPU ka twist", "GPUs were first built for video games, but their ability to do many calculations in parallel made them ideal for training neural networks."),
 ("AlphaZero", "AlphaZero taught itself chess, shogi and Go by playing against itself, reaching top level within hours in DeepMind's 2017 experiments."),
 ("ChatGPT ki launch", "ChatGPT launched on 30 November 2022 and reached one million users within days, one of the fastest-growing apps at the time."),
 ("Turing Award 2018", "Geoffrey Hinton, Yann LeCun and Yoshua Bengio received the 2018 Turing Award for their work on deep learning."),
 ("Mars rover aur AI", "NASA's Perseverance rover has an autonomous navigation system called AutoNav that helps it plan safe paths on Mars."),
 ("Hinton ka Nobel", "In 2024 Geoffrey Hinton and John Hopfield received the Nobel Prize in Physics for foundational work on artificial neural networks."),
 ("Face unlock ka raaz", "Phone face unlock turns your face into a numerical representation called an embedding and compares it with the stored one."),
 ("Self-driving ke levels", "Self-driving capability is described in levels from 0 to 5 by SAE International, where level 5 means full automation in all conditions."),
 ("Pixel kya dekhta hai", "To a computer an image is just a grid of numbers, one for each pixel, which a vision model learns to interpret."),
 ("Big data ki shuruaat", "Modern AI progress depends heavily on three things: large datasets, powerful hardware and better algorithms."),
]

def get_lesson_by_number(n):
    if 1 <= n <= TOTAL:
        return LESSONS[n - 1]
    return None

def _last(history, kind, field):
    for h in reversed(history):
        if h.get("type") == kind and isinstance(h.get(field), int):
            return h[field]
    return None

def get_next_lesson(history):
    """Next lesson = last POSTED lesson number + 1 (history is trimmed, so counting entries would break).
    After the last lesson the course starts again as a revision round."""
    last = _last(history, "lesson", "lesson_num")
    done = last if last is not None else len([h for h in history if h.get("type") == "lesson"])
    num = done % TOTAL + 1
    lesson = LESSONS[num - 1]
    nxt = LESSONS[num % TOTAL]
    log(f"Next lesson: #{num} - {lesson['title']} ({lesson['level']})")
    return lesson, num, nxt

def get_fun_fact(history):
    last = _last(history, "fun_fact", "fact_idx")
    idx = (last + 1 if last is not None else len([h for h in history if h.get("type") == "fun_fact"])) % len(FUN_FACTS)
    title, fact = FUN_FACTS[idx]
    return {"title": title, "facts": fact, "idx": idx}

if __name__ == "__main__":
    from collections import Counter
    print(TOTAL, "lessons", dict(Counter(l["level"] for l in LESSONS)), "|", len(FUN_FACTS), "fun facts")
