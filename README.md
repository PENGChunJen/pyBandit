<div align="center">

# PyBandit
**Real-valued Optimization by Subspace Projection and Multi-armed Bandit Techniques**


<p align="center">
  <a href="#view-demo">View Demo</a> •
  <a href="#contributing">Report Bug</a> •
  <a href="#contributing">Request Feature</a> 
</p>

[![CircleCI](https://circleci.com/gh/chunjenpeng/pyBandit.svg?style=shield&circle-token=aec3a2f38a41f3fbb8815e01f599e37557e526d3)](https://circleci.com/gh/chunjenpeng/pyBandit)
[![codecov](https://codecov.io/gh/Cinnamon/lib-table/branch/master/graph/badge.svg?token=KN45YUU644)](https://codecov.io/gh/Cinnamon/lib-table)
[![CodeFactor](https://www.codefactor.io/repository/github/cinnamon/lib-table/badge?s=6536d686d2c75baafdc7322c3dc7439c7b7ea65c)](https://www.codefactor.io/repository/github/cinnamon/lib-table)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/75a23726fbfd4ea4bece57e257e521e5)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Cinnamon/lib-table&amp;utm_campaign=Badge_Grade)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![version](https://img.shields.io/badge/version-v0.1.0-green)](https://github.com/chunjenpeng/pyBandit/tree/master/README.md)

</div>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#view-demo">View Demo</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
      <ul>
        <li><a href="#evolutionary-algorithms">Evolutionary Algorithms</a></li>
        <li><a href="#bandit-algorithms">Bandit Algorithms</a></li>
        <li><a href="#optimization-problems">Optimization Problems</a></li>
      </ul>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

### View Demo

[![Product Name Screen Shot][product-screenshot]](https://example.com)

There are many great README templates available on GitHub, however, I didn't find one that really suit my needs so I created this enhanced one. I want to create a README template so amazing that it'll be the last one you ever need -- I think this is it.

Here's why:
* Your time should be focused on creating something amazing. A project that solves a problem and helps others
* You shouldn't be doing the same tasks over and over like creating a README from scratch
* You should element DRY principles to the rest of your life :smile:

Of course, no one template will serve all projects since your needs may be different. So I'll be adding more in the near future. You may also suggest changes by forking this repo and creating a pull request or opening an issue. Thanks to all the people have have contributed to expanding this template!

A list of commonly used resources that I find helpful are listed in the acknowledgements.

### Built With

This section should list any major frameworks that you built your project using. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.
* [Bootstrap](https://getbootstrap.com)
* [JQuery](https://jquery.com)
* [Laravel](https://laravel.com)



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/your_username_/Project-Name.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```JS
   const API_KEY = 'ENTER YOUR API';
   ```



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/othneildrew/Best-README-Template/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

If you use this research/codebase, please cite our [paper](https://www.airitilibrary.com/Publication/alDetailedMesh?docid=U0001-3107201705294100).
```
@article{peng2017基於子空間映射與多臂吃角子老虎機技術之實數最佳化,
  title={基於子空間映射與多臂吃角子老虎機技術之實數最佳化},
  author={Peng, Chun-Jen},
  journal={臺灣大學電機工程學研究所學位論文},
  pages={1--77},
  year={2017},
  publisher={臺灣大學}
}
```


<!-- CONTACT -->
## Contact

Peng, Chun-Jen (Larry) - larrypengcj@gmail.com


<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [Taiwan Evolutionary Intelligence Laboratory](https://teilab.ee.ntu.edu.tw/#/home)
* [CMAES](https://github.com/CMA-ES/pycma): N. Hansen, S. D. Müller, and P. Koumoutsakos. Reducing the time complexity of the derandomized evolution strategy with covariance matrix adaptation (CMA-ES). Evolutionary computation, 11(1):1–18, 2003.
* SPSO: M. Clerc. Standard particle swarm optimisation. Retrieved from https://hal.archives-ouvertes.fr/hal-00764996/, 2012. 
* ACOR: K. Socha and M. Dorigo. Ant colony optimization for continuous domains. European journal of operational research, 185(3):1155–1173, 2008.


