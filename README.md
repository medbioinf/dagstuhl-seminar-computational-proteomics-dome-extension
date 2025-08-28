# FAIRness and EVERSE software quality metrics analysis of DOME extension break out group @ Dagstuhl Seminar 2025



## Abstrct
This breakout group on machine learning started out by identifying gaps between existing guidelines such as the DOME recommendations and FAIR4RS, which address reporting quality and FAIRness, but not software quality or the general question of sufficient novelty to warrant publication. Building on EVERSE’s research software quality framework, the group looked into maintainability aspects such as modularity, reusability, analysability, and testability as critical dimensions for ML, alongside adoption of community standards (e.g. HUPO-PSI formats) and benchmarking platforms like ProteoBench. FAIR principles were discussed in the context of both data and software. The group started to draft a manuscript that extends the recent article on “Open-Source and FAIR Research Software for Proteomics” (Perez-Riverol et al. 2025) and the earlier “Interpretation of the DOME Recommendations for Machine Learning in Proteomics and Metabolomics” (Palmblad et al. 2022), resulting from the 2021 Dagstuhl Seminar, by considering all research software quality dimensions in the EVERSE framework and synthesizes these considerations into recommendations, including a practical checklist for authors and reviewers, to promote the transparency, usability, and sustainable impact of ML in proteomics.

## Code

### Description
Collect some metrics of proteomic and genomic (ML) tools from bio.tools and github.com to compare the fairness and software quality dimensions.

#### Install

```shell
conda env create -f environments.yml
conda activate dagstuhl-dome-extension-metrics
```

#### Usage
Activate the conda environment, next
```shell
python -m dagstuhl-dome-extension-metrics
```

