"""
Sample Data Generator for RAG Agent

This module creates and processes sample data for the knowledge base.
"""

import os
import json
from typing import List, Dict, Any

from knowledge_base import KnowledgeBase

# Sample data categories and content
SAMPLE_DATA = [
    {
        "title": "Introduction to Machine Learning",
        "category": "technology",
        "content": """
Machine Learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide. The primary aim is to allow the computers to learn automatically without human intervention or assistance and adjust actions accordingly.

Machine learning algorithms are often categorized as supervised or unsupervised. Supervised algorithms require a data scientist or data analyst with machine learning skills to provide both input and desired output, in addition to furnishing feedback about the accuracy of predictions during algorithm training. Data scientists determine which variables, or features, the model should analyze and use to develop predictions. Once training is complete, the algorithm will apply what was learned to new data.

Unsupervised algorithms do not need to be trained with desired outcome data. Instead, they use an iterative approach called deep learning to review data and arrive at conclusions. Unsupervised learning algorithms are used for more complex processing tasks than supervised learning systems, including image recognition, speech-to-text, and natural language generation. These neural networks work by combing through millions of examples of training data and identifying often subtle correlations between many variables. Once trained, the algorithm can use its bank of associations to interpret new data.

Some popular machine learning algorithms include:
1. Linear Regression
2. Logistic Regression
3. Decision Tree
4. Support Vector Machines (SVM)
5. Naive Bayes
6. K-Nearest Neighbors (KNN)
7. K-Means
8. Random Forest
9. Neural Networks
10. Gradient Boosting algorithms like XGBoost and LightGBM
        """
    },
    {
        "title": "Understanding Deep Learning",
        "category": "technology",
        "content": """
Deep Learning is a subfield of machine learning concerned with algorithms inspired by the structure and function of the brain called artificial neural networks. Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.

Deep learning architectures such as deep neural networks, deep belief networks, recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, speech recognition, natural language processing, audio recognition, social network filtering, machine translation, bioinformatics, drug design, medical image analysis, material inspection and board game programs, where they have produced results comparable to and in some cases surpassing human expert performance.

Artificial Neural Networks (ANNs) are composed of multiple nodes, which imitate biological neurons of the human brain. The neurons are connected by links and they interact with each other. The nodes can take input data and perform simple operations on the data. The result of these operations is passed to other neurons. The output at each node is called its activation or node value.

Each link is associated with weight. ANNs are capable of learning, which takes place by altering weight values. The following are the important terminologies of ANN:

1. Neuron: Basic building block of ANN
2. Weights: Strength of connection between neurons
3. Bias: An extra input added to the neuron
4. Activation Function: Determines the output of a neuron
5. Layer: A group of neurons
6. Input Layer: First layer of the network
7. Hidden Layer: Intermediate layer between input and output layer
8. Output Layer: Final layer of the network

Deep learning models are trained by using large sets of labeled data and neural network architectures that learn features directly from the data without the need for manual feature extraction.
        """
    },
    {
        "title": "Natural Language Processing Fundamentals",
        "category": "technology",
        "content": """
Natural Language Processing (NLP) is a field of artificial intelligence that gives computers the ability to understand, interpret, and manipulate human language. NLP draws from many disciplines, including computer science and computational linguistics, in its pursuit to fill the gap between human communication and computer understanding.

The history of NLP generally started in the 1950s, although work can be found from earlier periods. In 1950, Alan Turing published an article titled "Computing Machinery and Intelligence" which proposed what is now called the Turing test as a criterion of intelligence. The Georgetown experiment in 1954 involved fully automatic translation of more than sixty Russian sentences into English. The authors claimed that within three or five years, machine translation would be a solved problem. However, real progress was much slower, and after the ALPAC report in 1966, which found that ten-year-long research had failed to fulfill the expectations, funding for machine translation was dramatically reduced.

Little further research in machine translation was conducted until the late 1980s when the first statistical machine translation systems were developed. During the 1970s, many programmers began to write "conceptual ontologies", which structured real-world information into computer-understandable data. Examples are MARGIE (Schank, 1975), SAM (Cullingford, 1978), PAM (Wilensky, 1978), TaleSpin (Meehan, 1976), QUALM (Lehnert, 1977), Politics (Carbonell, 1979), and Plot Units (Lehnert 1981).

Some of the main tasks in NLP include:

1. Text Classification: Assigning predefined categories to text documents
2. Text Extraction: Extracting structured information from unstructured text
3. Machine Translation: Translating text from one language to another
4. Named Entity Recognition: Identifying named entities in text
5. Sentiment Analysis: Identifying and extracting subjective information from text
6. Question Answering: Building systems that automatically answer questions posed by humans
7. Text Summarization: Producing a concise and fluent summary of a longer text document
8. Speech Recognition: Converting spoken language to text
9. Natural Language Generation: Converting information from computer databases into readable human language

Modern NLP applications include:
- Virtual assistants like Siri, Alexa, and Google Assistant
- Email filters that detect spam or malware
- Search engines that understand natural language queries
- Language translation services
- Customer service chatbots
- Text analytics for business intelligence
        """
    },
    {
        "title": "Retrieval-Augmented Generation (RAG) Systems",
        "category": "technology",
        "content": """
Retrieval-Augmented Generation (RAG) is a technique in natural language processing that combines the strengths of retrieval-based and generation-based approaches. RAG systems first retrieve relevant documents or passages from a knowledge base and then use these retrieved texts to augment the context provided to a language model for generating responses.

The key components of a RAG system include:

1. Knowledge Base: A collection of documents, articles, or passages that contain factual information. This knowledge base is indexed to allow for efficient retrieval.

2. Retriever: A component that takes a query and returns the most relevant documents or passages from the knowledge base. This is typically implemented using dense vector embeddings and similarity search.

3. Generator: A language model that takes the retrieved documents along with the original query to generate a coherent and informative response.

The advantages of RAG systems include:

- Factual Accuracy: By grounding generation in retrieved information, RAG systems can produce more factually accurate responses compared to pure generation approaches.
- Transparency: The retrieved documents provide a form of evidence or citation for the generated content, making the system more transparent.
- Updatability: The knowledge base can be updated without retraining the entire model, allowing the system to incorporate new information more easily.
- Reduced Hallucination: By providing relevant context, RAG systems can reduce the tendency of language models to generate plausible-sounding but incorrect information (hallucination).

RAG systems have been successfully applied in various applications, including:
- Question answering systems
- Conversational agents and chatbots
- Content generation tools
- Research assistants
- Customer support systems

The effectiveness of a RAG system depends on several factors:
- The quality and coverage of the knowledge base
- The performance of the retrieval mechanism
- The ability of the generator to effectively utilize the retrieved information
- The strategy for combining multiple retrieved documents

Recent advancements in RAG systems include:
- Multi-step retrieval processes
- Hybrid retrieval approaches combining sparse and dense retrievers
- Reranking mechanisms to improve retrieval precision
- Query reformulation techniques to improve retrieval recall
- Specialized training objectives for better integration of retrieved information
        """
    },
    {
        "title": "Climate Change: Causes and Effects",
        "category": "environment",
        "content": """
Climate change refers to long-term shifts in temperatures and weather patterns. These shifts may be natural, such as through variations in the solar cycle. But since the 1800s, human activities have been the main driver of climate change, primarily due to burning fossil fuels like coal, oil and gas.

Burning fossil fuels generates greenhouse gas emissions that act like a blanket wrapped around the Earth, trapping the sun's heat and raising temperatures. Examples of greenhouse gas emissions that are causing climate change include carbon dioxide and methane. These come from using gasoline for driving a car or coal for heating a building, for example. Clearing land and forests can also release carbon dioxide. Landfills for garbage are a major source of methane emissions. Energy, industry, transport, buildings, agriculture and land use are among the main emitters.

The effects of climate change are far-reaching and increasingly severe:

1. Rising Temperatures: The Earth's average surface temperature has risen about 1.1°C since the late 19th century, with the most pronounced warming occurring since the 1980s.

2. Changing Precipitation Patterns: Climate change is causing shifts in rainfall patterns, with some regions experiencing increased rainfall and flooding, while others face more severe droughts.

3. More Extreme Weather Events: The frequency and intensity of extreme weather events such as hurricanes, heatwaves, and wildfires are increasing due to climate change.

4. Sea Level Rise: Global sea levels have risen about 8-9 inches since 1880, with the rate accelerating in recent decades due to melting ice sheets and glaciers, as well as the expansion of seawater as it warms.

5. Ocean Acidification: The oceans have absorbed about 30% of the carbon dioxide released by human activities, leading to increased acidity that threatens marine ecosystems, particularly coral reefs and shellfish.

6. Biodiversity Loss: Climate change is altering habitats and disrupting ecosystems, contributing to species extinction and reducing biodiversity.

7. Human Health Impacts: Climate change affects human health through increased heat-related illnesses, expanded ranges of disease vectors like mosquitoes, reduced air quality, and food and water insecurity.

8. Economic Costs: The economic impacts of climate change include damage to infrastructure from extreme weather, reduced agricultural productivity, healthcare costs, and decreased labor productivity.

Addressing climate change requires both mitigation (reducing greenhouse gas emissions) and adaptation (adjusting to current and future climate impacts). International efforts like the Paris Agreement aim to limit global warming to well below 2°C above pre-industrial levels, with efforts to limit it to 1.5°C. This requires rapid transitions in energy, land, urban infrastructure, and industrial systems.
        """
    },
    {
        "title": "Renewable Energy Technologies",
        "category": "environment",
        "content": """
Renewable energy is energy derived from natural resources that are replenished at a higher rate than they are consumed. Sunlight, wind, rain, tides, waves, and geothermal heat are all renewable resources that can be harnessed for human use. Renewable energy stands in contrast to fossil fuels, which are being used far more quickly than they are being replenished.

The major types of renewable energy technologies include:

1. Solar Energy: Solar power harnesses the sun's energy to produce electricity. The two main solar technologies are:
   - Photovoltaic (PV) Systems: These directly convert sunlight into electricity using solar cells.
   - Concentrated Solar Power (CSP): These use mirrors or lenses to concentrate sunlight onto a small area, generating heat that drives a steam turbine connected to an electrical power generator.

2. Wind Energy: Wind turbines convert the kinetic energy in wind into mechanical power, which a generator converts into electricity. Wind farms can be built on land or offshore in bodies of water.

3. Hydropower: Hydroelectric power generates electricity by using the gravitational force of falling or flowing water. It's one of the oldest and largest sources of renewable energy.

4. Biomass Energy: Biomass is organic material from plants and animals, including crops, wood, and waste, that contains stored energy from the sun. When burned, this energy is released as heat.

5. Geothermal Energy: Geothermal energy utilizes heat from the Earth's core. Wells are drilled into underground reservoirs to tap steam and hot water, which can be used to drive turbines connected to electricity generators.

6. Ocean Energy: This includes:
   - Tidal Energy: Generated by the rise and fall of tides.
   - Wave Energy: Captures energy from ocean surface waves.
   - Ocean Thermal Energy Conversion (OTEC): Uses the temperature difference between cooler deep and warmer surface waters.

Advantages of renewable energy include:
- Reduced greenhouse gas emissions and air pollution
- Diversification of energy supply and reduced dependence on imported fuels
- Creation of economic development and jobs in manufacturing, installation, and more
- Access to energy in remote regions without expensive grid infrastructure

Challenges include:
- Intermittency of some sources (sun doesn't always shine, wind doesn't always blow)
- Higher initial capital costs compared to conventional energy systems
- Geographic limitations (some regions have better renewable resources than others)
- Storage needs to ensure reliable supply

The cost of renewable technologies has fallen dramatically in recent years, making them increasingly competitive with fossil fuels. Many countries have set ambitious targets for renewable energy adoption as part of their strategies to reduce greenhouse gas emissions and combat climate change.
        """
    },
    {
        "title": "The History of Ancient Egypt",
        "category": "history",
        "content": """
Ancient Egypt was a civilization of ancient North Africa, concentrated along the lower reaches of the Nile River, situated in the place that is now the country Egypt. Ancient Egyptian civilization followed prehistoric Egypt and coalesced around 3100 BC (according to conventional Egyptian chronology) with the political unification of Upper and Lower Egypt under Menes (often identified with Narmer).

The history of ancient Egypt can be divided into a series of stable kingdoms separated by periods of relative instability known as Intermediate Periods:

1. Early Dynastic Period (c. 3150-2686 BC): This period saw the development of the foundations of Egyptian culture, including the establishment of a capital at Memphis and the development of hieroglyphic writing.

2. Old Kingdom (c. 2686-2181 BC): Often referred to as the "Age of the Pyramids," this period saw the construction of the great pyramids, including the Step Pyramid of Djoser and the Great Pyramid of Giza. The Old Kingdom is known for strong central government and the beginning of the cult of the god-king.

3. First Intermediate Period (c. 2181-2055 BC): Following the collapse of the Old Kingdom, Egypt entered a period of weak central government and regional autonomy.

4. Middle Kingdom (c. 2055-1650 BC): A period of reunification and renewed prosperity, characterized by a new capital at Thebes, military expansion, and cultural flourishing.

5. Second Intermediate Period (c. 1650-1550 BC): This period included the Hyksos domination of Lower Egypt, while Upper Egypt remained under Egyptian rule.

6. New Kingdom (c. 1550-1069 BC): Egypt's most prosperous time and the peak of its power. This period saw the rule of famous pharaohs like Hatshepsut, Thutmose III, Akhenaten, Tutankhamun, and Ramesses II. Egypt expanded its territory into the Levant and Nubia.

7. Third Intermediate Period (c. 1069-664 BC): A period of political division, with power split between the pharaohs at Tanis and the High Priests of Amun at Thebes.

8. Late Period (664-332 BC): Egypt saw a series of foreign rulers, including Nubians, Persians, and finally, Alexander the Great's conquest in 332 BC.

9. Ptolemaic Period (332-30 BC): Rule by the Macedonian Ptolemaic dynasty, including Cleopatra VII.

10. Roman Period (30 BC-395 AD): Egypt became a province of the Roman Empire after Cleopatra's defeat.

Ancient Egyptian culture was sophisticated and complex, with remarkable achievements in art, architecture, medicine, mathematics, and literature. Religion played a central role in Egyptian life, with a complex pantheon of gods and goddesses and elaborate funerary practices based on beliefs about the afterlife. The Egyptians developed a 365-day calendar, practiced medicine that included surgery and dentistry, and created monumental architecture that still stands today.

The ancient Egyptian language was one of the longest continuously used languages in the world, evolving from Old Egyptian to Middle Egyptian (the classical form) to Late Egyptian, Demotic, and finally Coptic. Hieroglyphic writing, which combined logographic, syllabic, and alphabetic elements, was used for religious texts, while hieratic and later demotic scripts were used for everyday writing.

The legacy of ancient Egypt continues to influence modern culture, from architecture to literature to film, and its artifacts and monuments draw millions of tourists to Egypt each year.
        """
    },
    {
        "title": "The Renaissance Period in Europe",
        "category": "history",
        "content": """
The Renaissance was a period of European cultural, artistic, political, and scientific "rebirth" that spanned roughly from the 14th to the 17th century. The Renaissance began in Florence, Italy, in the late Middle Ages and later spread to the rest of Europe. The term Renaissance, meaning "rebirth" in French, first appeared in French historian Jules Michelet's 1855 work, Histoire de France, and referred to the revival of the values and artistic styles of classical antiquity during that period.

The Renaissance represented a cultural rebirth from the Middle Ages and an intellectual transformation that led to the Modern Age. It was characterized by a renewed interest in ancient Greek and Roman thought, an increased receptiveness to humanist philosophies, a commercial and urban revolution, and the decline of feudal institutions. The Renaissance is most closely associated with developments in philosophy, science, art, literature, music, and politics.

Key features of the Renaissance include:

1. Humanism: Renaissance humanism was an intellectual movement that emphasized the study of classical texts, human potential and achievement. Humanist scholars sought to create a citizenry able to speak and write with eloquence and clarity, thus capable of engaging in the civic life of their communities.

2. Art and Architecture: Renaissance art was characterized by realism, perspective, and the portrayal of human emotion. Artists like Leonardo da Vinci, Michelangelo, and Raphael created works that demonstrated these new techniques. Architecture saw a revival of classical forms, proportion, and symmetry.

3. Science and Technology: The Renaissance saw significant advances in science, with figures like Nicolaus Copernicus, Galileo Galilei, and Johannes Kepler challenging established views about the universe. The invention of the printing press by Johannes Gutenberg around 1440 revolutionized communication and facilitated the spread of new ideas.

4. Literature and Language: Writers like Dante Alighieri, Giovanni Boccaccio, and Francesco Petrarch helped establish the Italian vernacular as a literary language. In England, William Shakespeare and other playwrights created works that reflected Renaissance ideals and concerns.

5. Politics: Political thought during the Renaissance was marked by a more secular approach and an emphasis on rational analysis. Niccolò Machiavelli's "The Prince" (1513) represented a departure from medieval political thought with its pragmatic, and some would say cynical, advice to rulers.

6. Religion: The Renaissance coincided with the Protestant Reformation, which challenged the authority of the Catholic Church. The printing press played a crucial role in spreading reformist ideas.

The Renaissance spread from Italy to the rest of Europe in the late 15th and 16th centuries, with different regions experiencing it at different times and in different ways. The Northern Renaissance, for example, was characterized by a deeper religious piety and a focus on domestic interiors and portraiture in art.

The legacy of the Renaissance is immense, having laid the groundwork for the modern world in many ways. Its emphasis on humanism, rational inquiry, and individual achievement continues to influence Western culture today.
        """
    }
]

def create_sample_data_directory(base_dir: str = "../data/sample_data") -> str:
    """
    Create a directory for sample data files.
    
    Args:
        base_dir: Base directory for sample data
        
    Returns:
        Path to the created directory
    """
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def save_sample_data_to_files(data: List[Dict[str, Any]], directory: str) -> List[str]:
    """
    Save sample data to individual files.
    
    Args:
        data: List of sample data dictionaries
        directory: Directory to save files
        
    Returns:
        List of file paths
    """
    file_paths = []
    
    for i, item in enumerate(data):
        # Create a filename based on the title
        filename = f"{i+1:02d}_{item['title'].lower().replace(' ', '_')}.txt"
        file_path = os.path.join(directory, filename)
        
        # Write content to file
        with open(file_path, "w") as f:
            f.write(f"# {item['title']}\n\n")
            f.write(item['content'].strip())
        
        file_paths.append(file_path)
    
    # Also save the full dataset as JSON for reference
    json_path = os.path.join(directory, "sample_data.json")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    
    file_paths.append(json_path)
    
    return file_paths

def load_sample_data_to_knowledge_base(kb: KnowledgeBase, data: List[Dict[str, Any]]) -> List[str]:
    """
    Load sample data into the knowledge base.
    
    Args:
        kb: KnowledgeBase instance
        data: List of sample data dictionaries
        
    Returns:
        List of document IDs
    """
    documents = []
    metadatas = []
    
    for item in data:
        documents.append(item["content"])
        metadatas.append({
            "title": item["title"],
            "category": item["category"],
            "source": "sample_data"
        })
    
    # Add documents to knowledge base
    doc_ids = kb.add_documents(documents, metadatas)
    
    return doc_ids

def main():
    """
    Main function to generate and load sample data.
    """
    # Create sample data directory
    sample_dir = create_sample_data_directory()
    
    # Save sample data to files
    file_paths = save_sample_data_to_files(SAMPLE_DATA, sample_dir)
    print(f"Saved {len(file_paths)} sample data files to {sample_dir}")
    
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Load sample data to knowledge base
    doc_ids = load_sample_data_to_knowledge_base(kb, SAMPLE_DATA)
    print(f"Added {len(doc_ids)} documents to knowledge base")
    
    # Test search functionality
    test_query = "What are the components of a RAG system?"
    results = kb.search(test_query, n_results=2)
    
    print(f"\nTest Query: {test_query}")
    print(f"Found {len(results)} relevant documents:")
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Title: {result['metadata'].get('title', 'Unknown')}")
        print(f"Category: {result['metadata'].get('category', 'Unknown')}")
        print(f"Distance: {result['distance']}")
        print(f"Content snippet: {result['content'][:150]}...")

if __name__ == "__main__":
    main()
