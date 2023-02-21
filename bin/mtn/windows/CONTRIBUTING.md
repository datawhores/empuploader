# Contributing

Thank you for your interest in MTN. Here are a couple of ways you can do to make it better.  


## Comment issues

List [opened issues](https://gitlab.com/movie_thumbnailer/mtn/issues/?scope=all&state=opened) and  

 - share your experience  
 - add related links  
 - confirm others answers using "thumbs up"  
 - add helpful information related to the issue  

## Improve doc

Read the [README](https://gitlab.com/movie_thumbnailer/mtn/-/blob/devel/README.md) and [Wiki](https://gitlab.com/movie_thumbnailer/mtn/wikis/home) and check for errors, typos, etc. If you are not familiar with git and merge requests, you can send your correction via [email](mailto:movie_thumbnailer@gmx.com).

## Report bug

Download latest version and test it. If you find a bug, report an [issue](https://gitlab.com/movie_thumbnailer/mtn/issues). Fill in all important information to reproduce the bug. Use **-v** switch to print out debug information. Attach whole output as a file output.txt.  

<u>*Example:*</u>  

**OS:** FreeBSD  
**Command line:** `mtn -v -f DejaVuSans.ttf -c 3 -r 4 -g 5 -D 12 -o _preview.jpg video.mkv`  
**Link:** [http://link.to.video.mkv](http://link.to.video.mkv), [http://link.to.video_preview.jpg](http://link.to.video_preview.jpg)  
**Issue:** Invalid timestamps in last row of pictures  
**Attachment:**  output.txt  
**Output:**  (most interesting part of output)  
```
Movie Thumbnailer (mtn) 3.3.3
Compiled with: Lavc58.54.100 Lavf58.29.100 Lavu56.31.100 SwS5.5.100 GD:2.2.5

process_loop: video.mkv
make_thumbnail: video.mkv

[h264 @ 0x55e217825180] Reinit context to 768x576, pix_fmt: yuv420p
***dump_format_context, name: mov,mp4,m4a,3gp,3g2,mj2, long_name: QuickTime / MOV
File: video.mkv
Size: 1523171740 bytes (1.4 GiB), duration: 02:00:03, bitrate: 1691 kb/s
Stream 1: Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, mono, fltp, 82 kb/s (und)
Stream 0: Video: h264 (Main), 1 reference frame (avc1 / 0x31637661), yuv420p(left), 768x576 (0x0) [SAR 1:1 DAR 4:3], 1602 kb/s, 25.00 fps(r) (und)
start_time av: 0, duration av: 7203960000
start_time s: 0.00, duration s: 7203.96
***dump_stream, time_base: 1 / 25
   ...
***dump_codec_context h264, time_base: 1 / 50
frame_number: 2, width: 768, height: 576, sample_aspect_ratio 1/1**a**
shot 0: found_: 60148 (2406.00s), eff_: 60025 (2401.00s), dtime: 0.000
approx. decoded frames/s: inf
found_pts bottom: 60148
  *** avg_evade_try: 0.00
  0.42 s, 4.78 shots/s; output: video_mkv_preview.jpg
make_thumbnail: done
```

## Fix a bug

If you are familiar with C programming language and git, you can fix bug and send the patch:

* create gitlab account  
* fork mtn repository  
* checkout branch `devel`  
* Fix issue and make a [GitLab merge request](https://docs.gitlab.com/ee/gitlab-basics/add-merge-request.html) 

Suggested C style and coding standard: [SunOS](https://www.cis.upenn.edu/~lee/06cse480/data/cstyle.ms.pdf) or [OpenBSD](https://man.openbsd.org/style)

## How to store output to the file

Here is an example how to write mtn's output to the file out.log. Add verbose switch **-v** to the command line and redirect output to the file:

```
$ mtn -v -f font.ttf {all other switches} "movie.avi" &> out.log
```

