from os import path
from cv2 import cv2
from Katna.image import Image
from glob import glob
import operator
from PIL import Image as pil
from util import conf
from util.log_it import get_logger

logger = get_logger(__name__)

img_module = Image()

thumbnail_height = 180
thumbnail_width = 360

banner_ratios = [ '%d:1' % width for width in range(3,7)]
thumbnail_ratios = [ '4:3', '5:3']

movie_thumbnails =['fanart.jpg']

movie_thumbnail_order = [
    'clearart.png',
    'logo.png',
    'folder.jpg',
    'poster.jpg',
    'disc.png'
]

movie_banners = [  
      'logo.png'
    ]

movie_banner_order = [
    'fanart.jpg',
    'folder.jpg',
    'poster.jpg',
    'disc.png'
]

show_thumbnails = ['fanart.jpg']
show_thumbnail_order = [    
    'clearart.png',
    'landscape.jpg',
    'logo.png',
    'banner.jpg',
    'folder.jpg',
    'poster.jpg',
    'disc.png'
]

show_banners = [
    'banner.jpg',
    'logo.png'
]

show_banner_order = [
    'clearart.png',
    'landscape.jpg',
    'fanart.jpg',
    'folder.jpg',
    'poster.jpg',
    'disc.png'
]


def process_images(content_root):
    output_path = content_root.replace(conf.FINAL_DIR,conf.ASSETS_DIR)
    images_file_path = content_root.replace(conf.FINAL_DIR, conf.ASSET_TMP_DIR)
    if 'TV Shows' in images_file_path:
        process_type(images_file_path, show_banners, show_banner_order, output_path, banner_ratios, 'banner')
        process_type(images_file_path, show_thumbnails, show_thumbnail_order, output_path, thumbnail_ratios, 'thumbnail')
    else:
        process_type(images_file_path, movie_banners, movie_banner_order, output_path, banner_ratios, 'banner')
        process_type(images_file_path, movie_thumbnails, movie_thumbnail_order, output_path, thumbnail_ratios, 'thumbnail')


def process_type(images_file_path, acceptable_pics, crop_pics, file_output_path, ratios, output_name):
    accept_pic = next((path.join(images_file_path,img) for img in acceptable_pics if path.exists(path.join(images_file_path,img))), None)
    if accept_pic:
        logger.info('Found accepted %s - starting resize' % output_name)
        resize(accept_pic, file_output_path, output_name)
    else:
        logger.info('No accepted %s - starting crop' % output_name)
        cropable_pics = [ path.join(images_file_path,img) for img in crop_pics if path.exists(path.join(images_file_path,img))]
        crop_images(cropable_pics, ratios, file_output_path, output_name)


def resize(img_path, output_path, output_file_name):
    image = pil.open(img_path)
    ext = img_path.split('.')[-1]
    if "clearart" in img_path or "fanart" in img_path:
        image = image.resize([int(0.32 * s) for s in image.size])
    image.save(path.join(output_path, '%s.%s' % (output_file_name, ext)), quality=82, optimize=True)


def crop_images(img_paths, ratios, file_output_path, file_output_name):
    crop_result = [ (img, img_module.crop_image_with_aspect(
        file_path=img,
        crop_aspect_ratio=ratio,
        num_of_crops=1,
        down_sample_factor=5
    )) for img in img_paths 
    for ratio in ratios
    ]

    best_crop = max(crop_result, key=lambda res: res[1][0].score if res[1] else 0) 
    logger.info('Best crop from %s' % best_crop[0])
    img_loaded = cv2.imread(best_crop[0])
    ext_pic = best_crop[0].split('.')[-1]
    img_module.save_crop_to_disk(best_crop[1][0], img_loaded,
    file_path=file_output_path,
    file_name= file_output_name,
    file_ext='.%s' % ext_pic,
    )
    path_output = path.join(file_output_path, "%s.%s" % (file_output_name, ext_pic))
    image = pil.open(path_output)
    image.save(path.join(path_output), quality=82, optimize=True)

