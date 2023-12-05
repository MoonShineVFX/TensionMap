# TensionMap
Tension map node for Maya in Python, Write edge stretch / compression to vertex colors. 

* This plugin was originaly implemented in C++ by Anno Schachner, [original repo](https://github.com/wiremas/tension)

![alt text](https://github.com/wiremas/tension/blob/master/res/tension.gif "tension node")




* And was ported to Python by Alexander Smirnov, see this [gist](https://gist.github.com/Onefabis/57a4f9fe9eb1686505bbe6297d675671) and this [video](https://vimeo.com/315989835)
* Now here is the modified version of ours.


## Usage

![image](https://user-images.githubusercontent.com/3357009/130740748-7c5e7b22-0b1a-42aa-b3ec-eccf21f28fe0.png)

### Notes

To get proper evaluation, you may need to turn on original shape node's `caching` attrtibute.

![image](https://user-images.githubusercontent.com/3357009/130741205-8f921b5b-6489-420f-9ded-3671e0613797.png)

And may have to change the evaluation mode to `DG`.

![image](https://user-images.githubusercontent.com/3357009/130741291-a626fecf-19bb-4f54-b651-7e085516bc92.png)
