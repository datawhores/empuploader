/*  mtn - movie thumbnailer

    Copyright (C) 2007-2017 tuit <tuitfun@yahoo.co.th>, et al.	 		http://moviethumbnail.sourceforge.net/
    Copyright (C) 2017-2021 wahibre <wahibre@gmx.com>					https://gitlab.com/movie_thumbnailer/mtn/wikis	

    based on "Using libavformat and libavcodec" by Martin Böhme:
        http://www.inb.uni-luebeck.de/~boehme/using_libavcodec.html
        http://www.inb.uni-luebeck.de/~boehme/libavcodec_update.html
    and "An ffmpeg and SDL Tutorial":
        http://www.dranger.com/ffmpeg/
    and "Using GD with FFMPeg":
        http://cvs.php.net/viewvc.cgi/gd/playground/ffmpeg/
    and ffplay.c in ffmpeg
        Copyright (c) 2003 Fabrice Bellard
        http://ffmpeg.mplayerhq.hu/
    and gd.c in libGD
        http://cvs.php.net/viewvc.cgi/php-src/ext/gd/libgd/gd.c?revision=1.111&view=markup

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

// enable unicode functions in mingw
#ifdef WIN32
    #define UNICODE
    #define _UNICODE
#endif

#include <assert.h>
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <locale.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#include <getopt.h>

#include "libavutil/imgutils.h"
#include "libavutil/avutil.h"
#include "libavutil/display.h"
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
#include "libswscale/swscale.h"

#include "gd.h"

#define UTF8_FILENAME_SIZE (FILENAME_MAX*4)
#define LINESIZE_ALIGN 1
#define MAX_PACKETS_WITHOUT_PICTURE 1000

#define EXIT_SUCCESS 0
#define EXIT_WARNING 1
#define EXIT_ERROR   2


#ifdef WIN32
    unsigned int _CRT_fmode = _O_BINARY;  // default binary file including stdin, stdout, stderr
    #include <tchar.h>
    #include <windows.h>
    #ifdef _UNICODE
        #define UTF8_2_WC(wdst, src, size) MultiByteToWideChar(CP_UTF8, 0, (src), -1, (wdst), (size))
        #define WC_2_UTF8(dst, wsrc, size) WideCharToMultiByte(CP_UTF8, 0, (wsrc), -1, (dst), (size), NULL, NULL)
    #else
        #define UTF8_2_WC(dst, src, size) ((dst) = (src)) // cant be used to check required size
        #define WC_2_UTF8(dst, src, size) ((dst) = (src))
    #endif
#else
    #include "fake_tchar.h"
    #define UTF8_2_WC(dst, src, size) ((dst) = (src)) // cant be used to check required size
    #define WC_2_UTF8(dst, src, size) ((dst) = (src))
#endif


#ifndef MIN
#define MIN(a,b) ((a)<(b)?(a):(b))
#endif
#ifndef MAX
#define MAX(a,b) ((a)<(b)?(b):(a))
#endif

// newline character for info file
#ifdef WIN32
    #define NEWLINE "\r\n"
#else
    #define NEWLINE "\n"
#endif

#define EDGE_PARTS 6 // # of parts used in edge detection
#define EDGE_FOUND 0.001f // edge is considered found

typedef char TIME_STR[16];

typedef struct rgb_color
{
    int r;
    int g;
    int b;
} rgb_color;
typedef char color_str[7]; // "RRGGBB" (in hex)

#define COLOR_BLACK (rgb_color){0, 0, 0}
#define COLOR_GREY (rgb_color){128, 128, 128}
#define COLOR_WHITE (rgb_color){255, 255, 255}
#define COLOR_INFO (rgb_color){85, 85, 85}
#define IMAGE_EXTENSION_JPG ".jpg"
#define IMAGE_EXTENSION_PNG ".png"

typedef struct thumbnail
{
    gdImagePtr out_ip;
    char out_filename[UTF8_FILENAME_SIZE];
    char info_filename[UTF8_FILENAME_SIZE];
    char cover_filename[UTF8_FILENAME_SIZE];
    int out_saved;                          // 1 = out file is successfully saved
    int img_width, img_height;
    int txt_height;
    int column, row;
    double time_base;
    int64_t step_t;                         // in timebase units
    int shot_width_in,  shot_height_in;     // dimension stored in movie file
    int shot_width_out, shot_height_out;    // dimension  after possible rotation
    int center_gap;                         // horizontal gap to center the shots
    int idx;                                // index of the last shot; -1 = no shot
    int tiles_nr;                           // number of shots in thumbnail
    int rotation;                           // in degrees <-180; 180> stored in movie

    // dynamic
    int64_t *ppts; // array of pts value of each shot
} thumbnail; // thumbnail data & info

/* command line options & default values */
#define GB_A_RATIO (AVRational){0, 1}
AVRational gb_a_ratio = GB_A_RATIO;
#define GB_B_BLANK 0.8
double gb_b_blank = GB_B_BLANK;
#define GB_B_BEGIN 0.0
double gb_B_begin = GB_B_BEGIN; // skip this seconds from the beginning
#define GB_C_COLUMN 3
int gb_c_column = GB_C_COLUMN;
#define GB_C_CUT -1
double gb_C_cut = GB_C_CUT; // cut movie; <=0 off
#define GB_D_DEPTH -1
int gb_d_depth = GB_D_DEPTH; //directory depth
#define GB_D_EDGE 12
int gb_D_edge = GB_D_EDGE; // edge detection; 0 off; >0 on
//#define GB_E_EXT NULL
//char *gb_e_ext = GB_E_EXT;
#define GB_E_END 0.0
double gb_E_end = GB_E_END; // skip this seconds at the end
#ifdef __APPLE__
#	define SRC_DEF_FONTNAME "Tahoma Bold.ttf"
#else
#ifdef WIN32
#	define SRC_DEF_FONTNAME "tahomabd.ttf"
#else
#	define SRC_DEF_FONTNAME "DejaVuSans.ttf"
#endif
#endif

#ifdef MTN_DEF_FONTNAME
#   define GB_F_FONTNAME MTN_DEF_FONTNAME
#else
#   define GB_F_FONTNAME SRC_DEF_FONTNAME
#endif
char *gb_f_fontname = GB_F_FONTNAME;
rgb_color gb_F_info_color = COLOR_INFO; // info color
double gb_F_info_font_size = 9; // info font size
char *gb_F_ts_fontname = GB_F_FONTNAME; // time stamp fontname
rgb_color gb_F_ts_color = COLOR_WHITE; // time stamp color
rgb_color gb_F_ts_shadow = COLOR_BLACK; // time stamp shadow color
double gb_F_ts_font_size = 8; // time stamp font size
#define GB_G_GAP 0
int gb_g_gap = GB_G_GAP;
#define GB_H_HEIGHT 150
int gb_h_height = GB_H_HEIGHT; // mininum height of each shot; will reduce # of column to meet this height
int gb_H_human_filesize = 0; // filesize only in human readable size (KiB, MiB, GiB)
#define GB_I_INFO 1
int gb_i_info = GB_I_INFO; // 1 on; 0 off
#define GB_I_INDIVIDUAL 0
int gb_I_individual = GB_I_INDIVIDUAL; // 1 on; 0 off
#define GB_J_QUALITY 90
int gb_j_quality = GB_J_QUALITY;
#define GB_K_BCOLOR COLOR_WHITE
rgb_color gb_k_bcolor = GB_K_BCOLOR; // background color
#define GB_L_INFO_LOCATION 4
int gb_L_info_location = GB_L_INFO_LOCATION;
#define GB_L_TIME_LOCATION 1
int gb_L_time_location = GB_L_TIME_LOCATION;
#define GB_N_NORMAL 0
int gb_n_normal = GB_N_NORMAL; // normal priority; 1 normal; 0 lower
#define GB_N_SUFFIX NULL
char *gb_N_suffix = GB_N_SUFFIX; // info text file suffix
#define GB_X_FILENAME_USE_FULL 0
int gb_X_filename_use_full = GB_X_FILENAME_USE_FULL; // use full input filename (include extension)
#define GB_O_SUFFIX "_s.jpg"
char *gb_o_suffix = GB_O_SUFFIX;
#define GB_O_OUTDIR NULL
char *gb_O_outdir = GB_O_OUTDIR;
#ifdef WIN32
    #define GB_P_PAUSE 1
#else
    #define GB_P_PAUSE 0
#endif
int gb_p_pause = GB_P_PAUSE; // pause before exiting; 1 pause; 0 dont pause
#define GB_P_DONTPAUSE 0
int gb_P_dontpause = GB_P_DONTPAUSE; // dont pause; overide gb_p_pause
#define GB_Q_QUIET 0
int gb_q_quiet = GB_Q_QUIET; // 1 on; 0 off
#define GB_R_ROW 0
int gb_r_row = GB_R_ROW; // 0 = as many rows as needed
#define GB_S_STEP 120
int gb_s_step = GB_S_STEP; // less than 0 = every frame; 0 = step evenly to get column x row
#define GB_S_SELECT_VIDEO_STREAM 0
int gb_S_select_video_stream = GB_S_SELECT_VIDEO_STREAM;
#define GB_T_TIME 1
int gb_t_timestamp = GB_T_TIME; // 1 on; 0 off
#define GB_T_TEXT NULL
char *gb_T_text = GB_T_TEXT;
#define GB_V_VERBOSE 0
int gb_v_verbose = GB_V_VERBOSE; // 1 on; 0 off
int gb_V = GB_V_VERBOSE; // 1 on; 0 off
#define GB_W_WIDTH 1024
int gb_w_width = GB_W_WIDTH; // 0 = column * movie width
#define GB_W_OVERWRITE 1
int gb_W_overwrite = GB_W_OVERWRITE; // 1 = overwrite; 0 = dont overwrite
#define GB_Z_SEEK 0
int gb_z_seek = GB_Z_SEEK; // always use seek mode; 1 on; 0 off
#define GB_Z_NONSEEK 0
int gb_Z_nonseek = GB_Z_NONSEEK; // always use non-seek mode; 1 on; 0 off

/* long command line options */
int gb__shadow=-1;				// -1 off, 0 auto, >0 manual
int gb__transparent_bg=0;		//  0 off, 1 on
int gb__cover=0;                //  album art (cover image)
const char* gb__cover_suffix="_cover.jpg";


/* more global variables */
char *gb_argv0 = NULL;
char *gb_version = "3.4.1";
time_t gb_st_start = 0; // start time of program

/* misc functions */

/* strrstr not in mingw
*/
char *strlaststr (char *haystack, char *needle)
{
    // If needle is an empty string, the function returns haystack. -- from glibc doc
    if (0 == strlen(needle)) {
        return haystack;
    }

    char *start = haystack;
    char *found = NULL;
    char *prev = NULL;
    while ((found = strstr(start, needle)) != NULL) {
        prev = found;
        start++;
    }
    return prev;
}

char *format_color(rgb_color col)
{
    static char buf[7]; // FIXME
    sprintf(buf, "%02X%02X%02X", col.r, col.g, col.b);
    return buf; // FIXME
}

void format_time(double duration, TIME_STR str, char sep)
{
    if (duration < 0) {
        sprintf(str, "N/A");
    } else {
        int hours, mins, secs;
        //unsigned char hours, mins, secs;      // displays incorrect time
        secs = duration;
        mins = secs / 60;
        secs %= 60;
        hours = mins / 60;
        mins %= 60;

        snprintf(str, sizeof(TIME_STR), "%02d%c%02d%c%02d", hours, sep, mins, sep, secs);
    }
}

char *format_size(int64_t size)
{
    static char buf[23]; // FIXME
    char unit[]="B";

    if (size < 1024) {
        sprintf(buf, "%"PRId64" %s", size, unit);
    } else if (size < 1024*1024) {
        sprintf(buf, "%.0f ki%s", size/1024.0, unit);
    } else if (size < 1024*1024*1024) {
        sprintf(buf, "%.0f Mi%s", size/1024.0/1024, unit);
    } else {
        sprintf(buf, "%.1f Gi%s", size/1024.0/1024/1024, unit);
    }
    return buf;
}
/*
 * size: number of bites
 * Returnes formated string in b, kb, Mb or Gb.
 * Caller must free returned resource.
 */
char *format_size_f(int64_t size)
{
    char *buf = NULL;
    int bufflength;
    int needToPrint = 20;
    char unit[]="b";

    do
    {
        bufflength = needToPrint+1;
        buf = realloc(buf, bufflength);

        if (size < 1200) {
            needToPrint = snprintf(buf, bufflength,"%"PRId64" %s", size, unit);
        } else if (size < (int64_t)10000*1000) {
            needToPrint = snprintf(buf, bufflength,"%.0f k%s", size/1000.0, unit);
        } else if (size < (int64_t)10000*1000*1000) {
            needToPrint = snprintf(buf, bufflength,"%.0f M%s", size/1000.0/1000, unit);
        } else {
            needToPrint = snprintf(buf, bufflength,"%.1f G%s", size/1000.0/1000/1000, unit);
        }
    } while (needToPrint >= bufflength);

    return buf;
}
/*
return only the file name of the full path
FIXME: wont work in unix if filename has '\\', e.g. path = "hello \\ world";
*/
char *path_2_file(char *path)
{
    int len = strlen(path);
    char *slash = strrchr(path, '/');
    char *backslash = strrchr(path, '\\');
    if (NULL != slash || NULL != backslash) {
        char *last = (slash > backslash) ? slash : backslash;
        if (last - path + 1 < len) { // make sure last char is not '/' or '\\'
            return last + 1;
        }
    }
    return path;
}

/* 
copy n strings to dst
... must be char *
dst must be large enough
*/
char *strcpy_va(char *dst, int n, ...)
{
    va_list ap;
    int pos = 0;
    dst[pos] = '\0';
    va_start(ap, n);
    int i;
    for (i=0; i < n; i++) {
        char *s = va_arg(ap, char *);
        assert(NULL != s);
        strcat(dst, s);
    }
    va_end(ap);
    return dst;
}

/* 
return 1 if file is a regular file
return 0 if fail or is not 
*/
int is_reg(char *file)
{
#if defined(WIN32) && defined(_UNICODE)
    wchar_t file_w[FILENAME_MAX];
    UTF8_2_WC(file_w, file, FILENAME_MAX);
#else
    char *file_w = file;
#endif

    struct _stat buf;
    if (0 != _tstat(file_w, &buf)) {
        return 0;
    }
    return S_ISREG(buf.st_mode);
}

/* 
return 1 if file is a regular file and modified time >= st_time
return 0 if fail or is not 
*/
int is_reg_newer(char *file, time_t st_time)
{
#if defined(WIN32) && defined(_UNICODE)
    wchar_t file_w[FILENAME_MAX];
    UTF8_2_WC(file_w, file, FILENAME_MAX);
#else
    char *file_w = file;
#endif

    struct _stat buf;
    if (0 != _tstat(file_w, &buf)) {
        return 0;
    }
    return S_ISREG(buf.st_mode) && (difftime(buf.st_mtime, st_time) >= 0);
}

/* 
return 1 if file is a directory
return 0 if fail or is not a directory
FIXME: /c under msys is not a directory. why?
*/
int is_dir(char *file)
{
#if defined(WIN32) && defined(_UNICODE)
    wchar_t file_w[FILENAME_MAX];
    UTF8_2_WC(file_w, file, FILENAME_MAX);
#else
    char *file_w = file;
#endif

    struct _stat buf;
    if (0 != _tstat(file_w, &buf)) {
        return 0;
    }
    return S_ISDIR(buf.st_mode);
}

/*
*/
char *rem_trailing_slash(char *str)
{
#ifdef WIN32
    // mingw doesn't seem to be happy about trailing '/' or '\\'
    // strip trailing '/' or '\\' that might get added by shell filename completion for directories
    int last_index = strlen(str) - 1;
    // we need last '/' or '\\' for root drive "c:\"
    while (last_index > 2 && 
        ('/' == str[last_index] || '\\' == str[last_index])) {
        str[last_index--] = '\0';
    }
#endif
    return str;
}

/* mtn */

/* 
return pointer to a new cropped image. the original one is freed.
if error, return original and the original stays intact
*/
gdImagePtr crop_image(gdImagePtr ip, int new_width, int new_height)
{
    // cant find GD's crop, so we'll need to create a smaller image
    gdImagePtr new_ip = gdImageCreateTrueColor(new_width, new_height);
    if (NULL == new_ip) {
        //return NULL;
        // return the original should be better
        return ip;
    }
    gdImageCopy(new_ip, ip, 0, 0, 0, 0, new_width, new_height);
    gdImageDestroy(ip);
    return new_ip;
}

/*
returns height, or 0 if error
*/
int image_string_height(char *text, char *font, double size)
{
    int brect[8];

    if (NULL == text || 0 == strlen(text)) {
        return 0;
    }

    char *err = gdImageStringFT(NULL, &brect[0], 0, font, size, 0, 0, 0, text);
    if (NULL != err) {
        return 0;
    }
    return brect[3] - brect[7];
}

/*
position can be:
    1: lower left
    2: lower right
    3: upper right
    4: upper left
returns NULL if success, otherwise returns error message
*/
char *image_string(gdImagePtr ip, char *font, rgb_color color, double size, int position, int gap, char *text, int shadow, rgb_color shadow_color)
{
    int brect[8];

    int gd_color = gdImageColorResolve(ip, color.r, color.g, color.b);
    char *err = gdImageStringFT(NULL, &brect[0], gd_color, font, size, 0, 0, 0, text);
    if (NULL != err) {
        return err;
    }
    /*
    int width = brect[2] - brect[6];
    int height = brect[3] - brect[7];
    */

    int x, y;
    switch (position)
    {
    case 1: // lower left
        x = -brect[0] + gap;
        y = gdImageSY(ip) - brect[1] - gap;
        break;
    case 2: // lower right
        x = gdImageSX(ip) - brect[2] - gap;
        y = gdImageSY(ip) - brect[3] - gap;
        break;
    case 3: // upper right
        x = gdImageSX(ip) - brect[4] - gap;
        y = -brect[5] + gap;
        break;
    case 4: // upper left
        x = -brect[6] + gap;
        y = -brect[7] + gap;
        break;
    default:
        return "image_string's position can only be 1, 2, 3, or 4";
    }

    if (shadow) {
        int shadowx, shadowy;
        switch (position)
        {
        case 1: // lower left
            shadowx = x+1;
            shadowy = y;
            y = y-1;
            break;
        case 2: // lower right
            shadowx = x;
            shadowy = y;
            x = x-1;
            y = y-1;
            break;
        case 3: // upper right
            shadowx = x;
            shadowy = y+1;
            x = x-1;
            break;
        case 4: // upper left
            shadowx = x+1;
            shadowy = y+1;
            break;
        default:
            return "image_string's position can only be 1, 2, 3, or 4";
        }
        int gd_shadow = gdImageColorResolve(ip, shadow_color.r, shadow_color.g, shadow_color.b);
        err = gdImageStringFT(ip, &brect[0], gd_shadow, font, size, 0, shadowx, shadowy, text);
        if (NULL != err) {
            return err;
        }
    }

    return gdImageStringFT(ip, &brect[0], gd_color, font, size, 0, x, y, text);
}

/*
return 0 if image is saved
*/
int save_image(gdImagePtr ip, char *outname)
{
#if defined(WIN32) && defined(_UNICODE)
    wchar_t outname_w[FILENAME_MAX];
    UTF8_2_WC(outname_w, outname, FILENAME_MAX);
#else
    char *outname_w = outname;
#endif

    FILE *fp = _tfopen(outname_w, _TEXT("wb"));
    if (fp != NULL) {

        char* image_extension = strrchr(outname, '.');
        if(image_extension && strcmp(image_extension, ".png") == 0 )
            gdImagePngEx(ip, fp, 9);  // 9-best png compression
        else
            gdImageJpeg (ip, fp, gb_j_quality);

        if(fclose(fp) == 0)
            return 0;
        else
            av_log(NULL, AV_LOG_ERROR, "\n%s: closing output image '%s' failed: %s\n", gb_argv0, outname, strerror(errno));
    }
    else
        av_log(NULL, AV_LOG_ERROR, "\n%s: creating output image '%s' failed: %s\n", gb_argv0, outname, strerror(errno));

    return -1;
}
/*
pFrame must be a AV_PIX_FMT_RGB24 frame
*/
void FrameRGB_2_gdImage(AVFrame *pFrame, gdImagePtr ip, int width, int height)
{
    uint8_t *src = pFrame->data[0];
    int x, y;
    for (y = 0; y < height; y++) {
        for (x = 0; x < width * 3; x += 3) {
            gdImageSetPixel(ip, x / 3, y, gdImageColorResolve(ip, src[x], src[x + 1], src[x + 2]));
        }
        src += width * 3;
    }
}

/* initialize 
*/
void thumb_new(thumbnail *ptn)
{
    ptn->out_ip = NULL;
    ptn->out_filename[0]   = '\0';
    ptn->info_filename[0]  = '\0';
    ptn->cover_filename[0] = '\0';
    ptn->out_saved = 0;
    ptn->img_width = ptn->img_height = 0;
    ptn->txt_height = 0;
    ptn->column = ptn->row = 0;
    ptn->step_t = 0;
    ptn->shot_width_in  = ptn->shot_height_in = 0;
    ptn->shot_width_out = ptn->shot_height_out = 0;
    ptn->center_gap = 0;
    ptn->idx = -1;
    ptn->tiles_nr = 0;    
    ptn->rotation = 0;

    // dynamic
    ptn->ppts = NULL;
}

/* 
alloc dynamic data; must be called after all required static data is filled in
return -1 if failed
*/
int thumb_alloc_dynamic(thumbnail *ptn)
{
    ptn->ppts = malloc(ptn->column * ptn->row * sizeof(*(ptn->ppts)));
    if (NULL == ptn->ppts) {
        return -1;
    }
    return 0;
}

void thumb_cleanup_dynamic(thumbnail *ptn)
{
    if (NULL != ptn->ppts) {
        free(ptn->ppts);
        ptn->ppts = NULL;
    }
}

/* returns blured shadow on success, NULL otherwise	*/
gdImagePtr create_shadow_image(int background, int *INOUTradius, int width, int height)
{
    gdImagePtr shadow;
    int shW, shH, radius=*INOUTradius;

	if(radius >= 0)
	{
		if(radius == 0)
			*INOUTradius = radius = MAX((int)(((double)MIN(width, height)) * 0.03), 3);
		
		int shadowOffset = 2*radius+1;
		shW = width +(shadowOffset);
		shH = height+(shadowOffset);

		shadow = gdImageCreateTrueColor(shW, shH);
		if(shadow != NULL)
		{
			gdImageFilledRectangle(shadow, 0, 0, shW, shH, background);				//fill with background colour
			gdImageFilledRectangle(shadow, radius+1, radius+1, width, height, 0);	//fill black rectangle as a shadow
			//GaussianBlurred since libgd-2.1.1
			#if((GD_MAJOR_VERSION*1000000 + GD_MINOR_VERSION*1000 + GD_RELEASE_VERSION) >= 2001001)
			{
				gdImagePtr blurredShadow = gdImageCopyGaussianBlurred(shadow, radius, 0);			//blur shadow

				if(blurredShadow != NULL)
				{
					gdImageDestroy(shadow);
					av_log(NULL, AV_LOG_INFO, "  thumbnail shadow radius: %dpx %s", radius, NEWLINE);
					if(gb_g_gap < shadowOffset)
						av_log(NULL, AV_LOG_INFO, "  thumbnail shadow might be invisible. Consider increase gap between individual shots (-g %d).%s", shadowOffset, NEWLINE);
					return blurredShadow;
				}
				else
					av_log(NULL, AV_LOG_ERROR, "Can't blur Shadow Image!%s", NEWLINE);
			}
			#else
			{
				av_log(NULL, AV_LOG_INFO, "Can't blur Shadow Image. Libgd does not support blurring. Use version libgd-2.1.1 or newer.%s", NEWLINE);
				return shadow;
			}
            #endif
		}
		else
			av_log(NULL, AV_LOG_ERROR, "Couldn't create Image in Size %dx%d!%s", shW, shH, NEWLINE);
	}
	else
		av_log(NULL, AV_LOG_ERROR, "Shadow can't have negative value! (see option --shadow) %s", NEWLINE);

    return NULL;
}

/* 
add shot
because ptn->idx is the last index, this function assumes that shots will be added 
in increasing order.
*/
void thumb_add_shot(thumbnail *ptn, gdImagePtr ip, gdImagePtr thumbShadowIm, int idx, int64_t pts)
{
    int dstX = idx%ptn->column * (ptn->shot_width_out+gb_g_gap) + gb_g_gap + ptn->center_gap;
    int dstY = idx/ptn->column * (ptn->shot_height_out+gb_g_gap) + gb_g_gap
        + ((3 == gb_L_info_location || 4 == gb_L_info_location) ? ptn->txt_height : 0);

    if(gb__shadow > 0 && thumbShadowIm!=NULL)
		gdImageCopy(ptn->out_ip, thumbShadowIm, dstX+gb__shadow+1, dstY+gb__shadow+1, 0, 0, gdImageSX(thumbShadowIm), gdImageSY(thumbShadowIm));
    
    gdImageCopy(ptn->out_ip, ip, dstX, dstY, 0, 0, ptn->shot_width_out, ptn->shot_height_out);
    ptn->idx = idx;
    ptn->ppts[idx] = pts;
    ptn->tiles_nr++;
}

/*
perform convolution on pFrame and store result in ip
pFrame must be a AV_PIX_FMT_RGB24 frame
ip must be of the same size as pFrame
begin = upper left, end = lower right
filter should be a 2-dimensional but since we cant pass it without knowning the size, we'll use 1 dimension
modified from:
http://cvs.php.net/viewvc.cgi/php-src/ext/gd/libgd/gd.c?revision=1.111&view=markup
*/
void FrameRGB_convolution(AVFrame *pFrame, int width, int height, 
    float *filter, int filter_size, float filter_div, float offset,
    gdImagePtr ip, int xbegin, int ybegin, int xend, int yend)
{

    int x, y, i, j;
    float new_r, new_g, new_b;
    uint8_t *src = pFrame->data[0];

    for (y=ybegin; y<=yend; y++) {
        for(x=xbegin; x<=xend; x++) {
            new_r = new_g = new_b = 0;
            //float grey = 0;

            for (j=0; j<filter_size; j++) {
                int yv = MIN(MAX(y - filter_size/2 + j, 0), height - 1);
                for (i=0; i<filter_size; i++) {
                    int xv = MIN(MAX(x - filter_size/2 + i, 0), width - 1);
                    int pos = yv*width*3 + xv*3;
                    new_r += src[pos]   * filter[j * filter_size + i];
                    new_g += src[pos+1] * filter[j * filter_size + i];
                    new_b += src[pos+2] * filter[j * filter_size + i];
                    //grey += (src[pos] + src[pos+1] + src[pos+2])/3 * filter[j * filter_size + i];
                }
            }

            new_r = (new_r/filter_div)+offset;
            new_g = (new_g/filter_div)+offset;
            new_b = (new_b/filter_div)+offset;
            //grey = (grey/filter_div)+offset;

            new_r = (new_r > 255.0f)? 255.0f : ((new_r < 0.0f)? 0.0f:new_r);
            new_g = (new_g > 255.0f)? 255.0f : ((new_g < 0.0f)? 0.0f:new_g);
            new_b = (new_b > 255.0f)? 255.0f : ((new_b < 0.0f)? 0.0f:new_b);
            //grey = (grey > 255.0f)? 255.0f : ((grey < 0.0f)? 0.0f:grey);

            gdImageSetPixel(ip, x, y, gdImageColorResolve(ip, (int)new_r, (int)new_g, (int)new_b));
            //gdImageSetPixel(ip, x, y, gdTrueColor((int)new_r, (int)new_g, (int)new_b));
            //gdImageSetPixel(ip, x, y, gdTrueColor((int)grey, (int)grey, (int)grey));
        }
    }
}

/* begin = upper left, end = lower right
*/
float cmp_edge(gdImagePtr ip, int xbegin, int ybegin, int xend, int yend)
{
#define CMP_EDGE 208
    int count = 0;
    int i, j;
    for (j = ybegin; j <= yend; j++) {
        for (i = xbegin; i <= xend; i++) {
            int pixel = gdImageGetPixel(ip, i, j);
            if (gdImageRed(ip, pixel) >= CMP_EDGE 
                && gdImageGreen(ip, pixel) >= CMP_EDGE
                && gdImageBlue(ip, pixel) >= CMP_EDGE) {
                count++;
            }
        }
    }
    return (float)count / (yend - ybegin + 1) / (xend - xbegin + 1);
}

int is_edge(float *edge, float edge_found)
{
    if (gb_V) { // DEBUG
        return 1;
    }
    int count = 0;
    int i;
    for (i = 0; i < EDGE_PARTS; i++) {
        if (edge[i] >= edge_found) {
            count++;
        }
    }
    if (count >= 2) {
        return count;
    }
    return 0;
}

/*
pFrame must be an AV_PIX_FMT_RGB24 frame
http://student.kuleuven.be/~m0216922/CG/
http://www.pages.drexel.edu/~weg22/edge.html
http://student.kuleuven.be/~m0216922/CG/filtering.html
http://cvs.php.net/viewvc.cgi/php-src/ext/gd/libgd/gd.c?revision=1.111&view=markup
*/
gdImagePtr detect_edge(AVFrame *pFrame, const thumbnail* const tn, float *edge, float edge_found)
{
    int width =  tn->shot_width_in;
    int height = tn->shot_height_in;
    static float filter[] = {
         0,-1, 0,
        -1, 4,-1,
         0,-1, 0
    };
#define FILTER_SIZE 3 // 3x3
#define FILTER_DIV 1
#define OFFSET 128
    static int init_filter = 0; // FIXME
    if (0 == init_filter) {
        init_filter = 1;
        filter[1] = -gb_D_edge/4.0f;
        filter[3] = -gb_D_edge/4.0f;
        filter[4] =  gb_D_edge;
        filter[5] = -gb_D_edge/4.0f;
        filter[7] = -gb_D_edge/4.0f;
    }

    gdImagePtr ip = gdImageCreateTrueColor(width, height);
    if (NULL == ip) {
        av_log(NULL, AV_LOG_ERROR, "  gdImageCreateTrueColor failed%s", NEWLINE);
        return NULL;
    }
    if (gb_v_verbose > 0) {
        FrameRGB_2_gdImage(pFrame, ip, width, height);
    }

    int i;
    for (i = 0; i < EDGE_PARTS; i++) {
        edge[i] = 1;
    }

    // check 6 parts to speed this up & to improve correctness
    int y_size = height/10;
    int ya = y_size*2;
    int yb = y_size*4;
    int yc = y_size*6;
    int x_crop = width/8;

    // only find edge if neccessary
    int parts[EDGE_PARTS][4] = {
        //xbegin, ybegin, xend, yend
        {x_crop, ya, width/2, ya+y_size},
        {width/2+1, ya+y_size, width-x_crop, ya+2*y_size},
        {x_crop, yb, width/2, yb+y_size},
        {width/2+1, yb+y_size, width-x_crop, yb+2*y_size},
        {x_crop, yc, width/2, yc+y_size},
        {width/2+1, yc+y_size, width-x_crop, yc+2*y_size},
    };
    int count = 0;
    for (i = 0; i < EDGE_PARTS && count < 2; i++) {
        FrameRGB_convolution(pFrame, width, height, filter, FILTER_SIZE, FILTER_DIV, OFFSET, 
            ip, parts[i][0], parts[i][1], parts[i][2], parts[i][3]);
        edge[i] = cmp_edge(ip, parts[i][0], parts[i][1], parts[i][2], parts[i][3]);
        if (edge[i] >= edge_found) {
            count++;
        }
    }
    return ip;
}

/* for debuging
void save_AVFrame(const AVFrame* const pFrame, int src_width, int src_height, int pix_fmt,
    char *filename, int dst_width, int dst_height)
{
    AVFrame *pFrameRGB = NULL;
    uint8_t *rgb_buffer = NULL;
    struct SwsContext *pSwsCtx = NULL;
    gdImagePtr ip = NULL;

    pFrameRGB = av_frame_alloc();
    if (pFrameRGB == NULL) {
        av_log(NULL, AV_LOG_ERROR, "  couldn't allocate a video frame %s", NEWLINE);
        goto cleanup;
    }
    int rgb_bufsize = av_image_get_buffer_size(AV_PIX_FMT_RGB24, dst_width, dst_height, av_image_get_buffer_size_linesize);
    rgb_buffer = av_malloc(rgb_bufsize);
    if (NULL == rgb_buffer) {
        av_log(NULL, AV_LOG_ERROR, "  av_malloc %d bytes failed\n", rgb_bufsize);
        goto cleanup;
    }
    //  DEPRECATED avpicture_fill -> av_image_fill_arrays
//    avpicture_fill((AVPicture *) pFrameRGB, rgb_buffer, AV_PIX_FMT_RGB24, dst_width, dst_height);
    av_image_fill_arrays(pFrameRGB->data, pFrameRGB->linesize, rgb_buffer, pFrameRGB->format, pFrameRGB->width, pFrameRGB->height, av_image_get_buffer_size_linesize);

    pSwsCtx = sws_getContext(src_width, src_height, pix_fmt,
        dst_width, dst_height, AV_PIX_FMT_RGB24, SWS_BILINEAR, NULL, NULL, NULL);
    if (NULL == pSwsCtx) { // sws_getContext is not documented
        av_log(NULL, AV_LOG_ERROR, "  sws_getContext failed\n");
        goto cleanup;
    }

    sws_scale(pSwsCtx, pFrame->data, pFrame->linesize, 0, src_height, 
        pFrameRGB->data, pFrameRGB->linesize);
    ip = gdImageCreateTrueColor(dst_width, dst_height);
    if (NULL == ip) {
        av_log(NULL, AV_LOG_ERROR, "  gdImageCreateTrueColor failed: width %d, height %d\n", dst_width, dst_height);
        goto cleanup;
    }
    FrameRGB_2_gdImage(pFrameRGB, ip, dst_width, dst_height);
    int ret = save_jpg(ip, filename);
    if (0 != ret) {
        av_log(NULL, AV_LOG_ERROR, "  save_jpg failed: %s\n", filename);
        goto cleanup;
    }

  cleanup:
    if (NULL != ip)
        gdImageDestroy(ip);
    if (NULL != pSwsCtx)
        sws_freeContext(pSwsCtx); // do we need to do this?
    if (NULL != rgb_buffer)
        av_free(rgb_buffer);
    if (NULL != pFrameRGB)
        av_free(pFrameRGB);
}
*/


/* av_pkt_dump_log()?? */
void dump_packet(AVPacket *p, AVStream * ps)
{
    /* from av_read_frame()
    pkt->pts, pkt->dts and pkt->duration are always set to correct values in 
    AVStream.timebase units (and guessed if the format cannot provided them). 
    pkt->pts can be AV_NOPTS_VALUE if the video format has B frames, so it is 
    better to rely on pkt->dts if you do not decompress the payload.
    */
    av_log(NULL, AV_LOG_VERBOSE, "***dump_packet: pos:%"PRId64"%s", p->pos, NEWLINE);
    av_log(NULL, AV_LOG_VERBOSE, "pts tb: %"PRId64", dts tb: %"PRId64", duration tb: %"PRId64"%s",
        p->pts, p->dts, p->duration, NEWLINE);
    av_log(NULL, AV_LOG_VERBOSE, "pts s: %.2f, dts s: %.2f, duration s: %.2f%s",
        p->pts * av_q2d(ps->time_base), p->dts * av_q2d(ps->time_base), 
        p->duration * av_q2d(ps->time_base), NEWLINE); // pts can be AV_NOPTS_VALUE
}

void dump_codec_context(AVCodecContext * p)
{
    if(p->codec == 0)
        av_log(NULL, AV_LOG_VERBOSE, "***dump_codec_context: codec = ?0?\n");
    else
        av_log(NULL, AV_LOG_VERBOSE, "***dump_codec_context %s, time_base: %d / %d\n", p->codec->name,
            p->time_base.num, p->time_base.den);

    av_log(NULL, AV_LOG_VERBOSE, "frame_number: %d, width: %d, height: %d, sample_aspect_ratio %d/%d%s\n",
        p->frame_number, p->width, p->height, p->sample_aspect_ratio.num, p->sample_aspect_ratio.den,
        (0 == p->sample_aspect_ratio.num) ? "" : "**a**");
}

/*
void dump_index_entries(AVStream * p)
{
    int i;
    double diff = 0;
    for (i=0; i < p->nb_index_entries; i++) { 
        AVIndexEntry *e = p->index_entries + i;
        double prev_ts = 0, cur_ts = 0;
        cur_ts = e->timestamp * av_q2d(p->time_base);
        //assert(cur_ts > 0);
        diff += cur_ts - prev_ts;
        if (i < 20) { // show only first 20
            av_log(NULL, AV_LOG_VERBOSE, "    i: %2d, pos: %8"PRId64", timestamp tb: %6"PRId64", timestamp s: %6.2f, flags: %d, size: %6d, min_distance: %3d\n",
                i, e->pos, e->timestamp, e->timestamp * av_q2d(p->time_base), e->flags, e->size, e->min_distance);
        }
        prev_ts = cur_ts;
    }
    av_log(NULL, AV_LOG_VERBOSE, "  *** nb_index_entries: %d, avg. timestamp s diff: %.2f\n", p->nb_index_entries, diff / p->nb_index_entries);
}
*/

//based on dump.c: static void dump_sidedata(void *ctx, AVStream *st, const char *indent)
double get_stream_rotation(AVStream *st)
{
    double rotation = 0.0;

    if (st->nb_side_data)
    {

        int i;
        for(i=0; i < st->nb_side_data; i++ )
        {
            AVPacketSideData sd = st->side_data[i];

            if(sd.type == AV_PKT_DATA_DISPLAYMATRIX) {
                rotation = av_display_rotation_get((int32_t *)sd.data);
                break;
            }
        }
    }

    return rotation;
}

void dump_stream(AVStream * p)
{
    av_log(NULL, AV_LOG_VERBOSE, "***dump_stream, time_base: %d / %d\n", 
        p->time_base.num, p->time_base.den);
    av_log(NULL, AV_LOG_VERBOSE, "cur_dts tb?: %"PRId64", start_time tb: %"PRId64", duration tb: %"PRId64", nb_frames: %"PRId64"\n",
        p->cur_dts, p->start_time, p->duration, p->nb_frames);
    // get funny results here. use format_context's.
    av_log(NULL, AV_LOG_VERBOSE, "cur_dts s?: %.2f, start_time s: %.2f, duration s: %.2f\n",
        p->cur_dts * av_q2d(p->time_base), p->start_time * av_q2d(p->time_base), 
        p->duration * av_q2d(p->time_base)); // duration can be AV_NOPTS_VALUE 
    // field pts in AVStream is for encoding
}

/*
set scale source width & height (scaled_w and scaled_h)
*/
void calc_scale_src(int width, int height, AVRational ratio, int *scaled_w, int *scaled_h)
{
    // mplayer dont downscale horizontally. however, we'll always scale
    // horizontally, up or down, which is the same as mpc's display and 
    // vlc's snapshot. this should make square pixel for both pal & ntsc.
    *scaled_w = width;
    *scaled_h = height;
    if (0 != ratio.num) { // ratio is defined
        assert(ratio.den != 0);
        *scaled_w = av_q2d(ratio) * width + 0.5; // round nearest
    }
}

long
get_bitrate_from_metadata(const AVDictionary *dict)
{
    if(av_dict_count(dict) > 0)
    {
        char *bps_value = NULL;
        AVDictionaryEntry* e = NULL;

        e = av_dict_get(dict, "BPS-eng", NULL, AV_DICT_IGNORE_SUFFIX);

        if(e)
            bps_value = e->value;
        else
        {
            e = av_dict_get(dict, "BPS", NULL, AV_DICT_IGNORE_SUFFIX);

            if(e)
                bps_value = e->value;
        }

        if(bps_value)
            return atol(bps_value);
    }

    return 0;
}

AVCodecContext* get_codecContext_from_codecParams(AVCodecParameters* pCodecPar)
{
    AVCodecContext *pCodecContext;

    pCodecContext = avcodec_alloc_context3(NULL);
    if(!pCodecContext)
    {
        av_log(NULL, AV_LOG_ERROR, "Couldn't alocate codec context %s", NEWLINE);
        return NULL;
    }

    if(avcodec_parameters_to_context(pCodecContext, pCodecPar) <0 )
    {
        avcodec_free_context(&pCodecContext);
        return NULL;
    }

    return pCodecContext;
}

/*
modified from libavformat's dump_format
*/
void get_stream_info_type(AVFormatContext *ic, enum AVMediaType type, char *buf, AVRational sample_aspect_ratio)
{
    char sub_buf[1024] = {'\0',}; //FIXME char sub_buf[1024]
    unsigned int i;
    AVCodecContext *pCodexCtx=NULL;
    char subtitles_separator[3] = {'\0',};

    for(i=0; i<ic->nb_streams; i++) {
        char codec_buf[256];
        int flags = ic->iformat->flags;
        AVStream *st = ic->streams[i];
        AVDictionaryEntry *language = av_dict_get(st->metadata, "language", NULL, 0);

        if (type != st->codecpar->codec_type) {
            continue;
        }

        pCodexCtx = get_codecContext_from_codecParams(st->codecpar);

        if (AVMEDIA_TYPE_SUBTITLE  == st->codecpar->codec_type) {
            if (language != NULL) {
                AVDictionaryEntry *subentry_title = av_dict_get(st->metadata, "title", NULL, 0);
                if(subentry_title && strcasecmp(subentry_title->value, "sub"))
                    sprintf(sub_buf + strlen(sub_buf), "%s%s (%s)", subtitles_separator, language->value, subentry_title->value);
                else
                    sprintf(sub_buf + strlen(sub_buf), "%s%s", subtitles_separator, language->value);

                strcpy(subtitles_separator, ", ");
            }
            else {
                //ignore for now; language seem to be missing in .vob files
                //sprintf(sub_buf + strlen(sub_buf), "? ");
            }
            continue;
        }

        strcat(buf, NEWLINE);

        if (gb_v_verbose > 0) {
            sprintf(buf + strlen(buf), "Stream %d", i);
            if (flags & AVFMT_SHOW_IDS) {
                sprintf(buf + strlen(buf), "[0x%x]", st->id);
            }
            /*
            int g = ff_gcd(st->time_base.num, st->time_base.den);
            sprintf(buf + strlen(buf), ", %d/%d", st->time_base.num/g, st->time_base.den/g);
            */
            sprintf(buf + strlen(buf), ": ");
        }

        avcodec_string(codec_buf, sizeof(codec_buf), pCodexCtx, 0);

/* re-enable SAR & DAR
        // remove [SAR DAR] from string, it's not very useful.
        char *begin = NULL, *end = NULL;
        if ((begin=strstr(codec_buf, " [SAR")) != NULL
            && (end=strchr(begin, ']')) != NULL) {
            while (*++end != '\0') {
                *begin++ = *end;
            }
            *begin = '\0';
        }
*/
        strcat(buf, codec_buf);

        /* if bitrate is missing, try to search elsewhere */
        if((AVMEDIA_TYPE_AUDIO  == st->codecpar->codec_type || AVMEDIA_TYPE_VIDEO  == st->codecpar->codec_type )
        &&  st->codecpar->bit_rate <= 0)
        {
            char bitratebuff[100];
            long metadata_bitrate = get_bitrate_from_metadata(st->metadata);

            if(metadata_bitrate > 0)
            {
                char *formated_bitrate_size = format_size_f(metadata_bitrate);
                snprintf(bitratebuff, sizeof(bitratebuff),", %s/s", formated_bitrate_size);
                strcat(buf, bitratebuff);
                free(formated_bitrate_size);
            }
        }

        if (st->codecpar->codec_type == AVMEDIA_TYPE_VIDEO ){
            if (st->r_frame_rate.den && st->r_frame_rate.num)
                sprintf(buf + strlen(buf), ", %5.2f fps(r)", av_q2d(st->r_frame_rate));
            else
                sprintf(buf + strlen(buf), ", %5.2f fps(c)", 1/av_q2d(st->time_base));

            // show aspect ratio
            int scaled_src_width, scaled_src_height;

            calc_scale_src(st->codecpar->width, st->codecpar->height, sample_aspect_ratio,
                &scaled_src_width, &scaled_src_height);

            if (scaled_src_width != st->codecpar->width || scaled_src_height != st->codecpar->height) {
                sprintf(buf + strlen(buf), " => %dx%d", scaled_src_width, scaled_src_height);
            }
        }
        if (language != NULL) {
            sprintf(buf + strlen(buf), " (%s)", language->value);
        }
    } //for

    if (0 < strlen(sub_buf)) {
        sprintf(buf + strlen(buf), "\nSubtitles: %s", sub_buf);
    }

    if(pCodexCtx)
        avcodec_free_context(&pCodexCtx);
}


/*
modified from libavformat's dump_format
*/
char *get_stream_info(AVFormatContext *ic, char *url, int strip_path, AVRational __attribute__((unused)) sample_aspect_ratio)
{
    static char buf[4096]; // FIXME: this is also used for all text at the top
    int duration = -1;

    char *file_name = url;
    if (1 == strip_path) {
        file_name = path_2_file(url);
    }

    int64_t file_size = avio_size(ic->pb);

    sprintf(buf, "File: %s", file_name);
    /* file format
    sprintf(buf + strlen(buf), " (%s)", ic->iformat->name);*/

    if(gb_H_human_filesize)
        /* File size only in MiB, GiB, ... */
        sprintf(buf + strlen(buf), "%sSize: %s", NEWLINE, format_size(file_size));
    else
        /* File size i bytes and MiB */
        sprintf(buf + strlen(buf), "%sSize: %"PRId64" bytes (%s)", NEWLINE, file_size, format_size(file_size));


    if (ic->duration != AV_NOPTS_VALUE) {
        int hours, mins, secs;
        duration = secs = ic->duration / AV_TIME_BASE;
        mins = secs / 60;
        secs %= 60;
        hours = mins / 60;
        mins %= 60;
        sprintf(buf + strlen(buf), ", duration: %02d:%02d:%02d", hours, mins, secs);
    } else {
        sprintf(buf + strlen(buf), ", duration: N/A");
    }
    /*
    if (ic->start_time != AV_NOPTS_VALUE) {
        int secs, us;
        secs = ic->start_time / AV_TIME_BASE;
        us = ic->start_time % AV_TIME_BASE;
        sprintf(buf + strlen(buf), ", start: %d.%06d", secs, (int)av_rescale(us, 1000000, AV_TIME_BASE));
    }
    */

    // some formats, eg. flv, dont seem to support bit_rate, so we'll prefer to 
    // calculate from duration.
    // is this ok? probably not ok with .vob files when duration is wrong. DEBUG


    if (ic->bit_rate) {
        sprintf(buf + strlen(buf), ", bitrate: %"PRId64" kb/s", ic->bit_rate / 1000);
    } else if (duration > 0) {
        sprintf(buf + strlen(buf), ", avg.bitrate: %.0f kb/s", (double) file_size * 8.0 / duration / 1000);
    } else {
        strcat(buf, ", bitrate: N/A");
    }

    get_stream_info_type(ic, AVMEDIA_TYPE_AUDIO,   buf, sample_aspect_ratio);
    get_stream_info_type(ic, AVMEDIA_TYPE_VIDEO,   buf, sample_aspect_ratio);
    get_stream_info_type(ic, AVMEDIA_TYPE_SUBTITLE,buf, sample_aspect_ratio);

    //strfmon(buf + strlen(buf), 100, "strfmon: %!i\n", avio_size(ic->pb));
    return buf;
}

void dump_format_context(AVFormatContext *p, int __attribute__((unused)) index, char *url, int __attribute__((unused)) is_output)
{
    //av_log(NULL, AV_LOG_ERROR, "\n");
    av_log(NULL, AV_LOG_VERBOSE, "***dump_format_context, name: %s, long_name: %s\n", 
        p->iformat->name, p->iformat->long_name);
    //dump_format(p, index, url, is_output);

    // dont show scaling info at this time because we dont have the proper sample_aspect_ratio
    av_log(NULL, AV_LOG_INFO, "%s%s", get_stream_info(p, url, 0, GB_A_RATIO), NEWLINE);

    av_log(NULL, AV_LOG_VERBOSE, "start_time av: %"PRId64", duration av: %"PRId64"\n",
        p->start_time, p->duration);
    av_log(NULL, AV_LOG_VERBOSE, "start_time s: %.2f, duration s: %.2f\n",
        (double) p->start_time / AV_TIME_BASE, (double) p->duration / AV_TIME_BASE);

    AVDictionaryEntry* track    = av_dict_get(p->metadata, "track",     NULL, 0);
    AVDictionaryEntry* title    = av_dict_get(p->metadata, "title",     NULL, 0);
    AVDictionaryEntry* author   = av_dict_get(p->metadata, "author",    NULL, 0);
    AVDictionaryEntry* copyright= av_dict_get(p->metadata, "copyright", NULL, 0);
    AVDictionaryEntry* comment  = av_dict_get(p->metadata, "comment",   NULL, 0);
    AVDictionaryEntry* album    = av_dict_get(p->metadata, "album",     NULL, 0);
    AVDictionaryEntry* year     = av_dict_get(p->metadata, "year",      NULL, 0);
    AVDictionaryEntry* genre    = av_dict_get(p->metadata, "genre",     NULL, 0);

    if (track != NULL)
        av_log(NULL, AV_LOG_INFO, "  Track: %s\n",     track->value);
    if (title != NULL)
        av_log(NULL, AV_LOG_INFO, "  Title: %s\n",     title->value);
    if (author != NULL)
        av_log(NULL, AV_LOG_INFO, "  Author: %s\n",    author->value);
    if (copyright != NULL)
        av_log(NULL, AV_LOG_INFO, "  Copyright: %s\n", copyright->value);
    if (comment != NULL)
        av_log(NULL, AV_LOG_INFO, "  Comment: %s\n",   comment->value);
    if (album != NULL)
        av_log(NULL, AV_LOG_INFO, "  Album: %s\n",     album->value);
    if (year != NULL)
        av_log(NULL, AV_LOG_INFO, "  Year: %s\n",      year->value);
    if (genre != NULL)
        av_log(NULL, AV_LOG_INFO, "  Genre: %s\n",     genre->value);
}

/*
*/
double uint8_cmp(uint8_t *pa, uint8_t *pb, uint8_t *pc, int n)
{
    int i, same = 0;
    for (i=0; i<n; i++) {
        int diffab = pa[i] - pb[i];
        int diffac = pa[i] - pc[i];
        int diffbc = pb[i] - pb[i];

        if ((diffab > -20) && (diffab < 20) &&
            (diffac > -20) && (diffac < 20) &&
            (diffbc > -20) && (diffbc < 20)) {
            same++;
        }
    }
    return (double)same / n;
}

/*
return sameness of the frame; 1 means the frame is the same in all directions, i.e. blank
pFrame must be an AV_PIX_FMT_RGB24 frame
*/
double blank_frame(AVFrame *pFrame, int width, int height)
{
    uint8_t *src = pFrame->data[0];
    int hor_size = height/11 * width * 3;
    uint8_t *pa = src+hor_size*2;
    uint8_t *pb = src+hor_size*5;
    uint8_t *pc = src+hor_size*8;
    double same = .4*uint8_cmp(pa, pb, pc, hor_size);
    int ver_size = hor_size/3;
    same += .6/3*uint8_cmp(pa, pa + ver_size, pa + ver_size*2, ver_size);
    same += .6/3*uint8_cmp(pb, pb + ver_size, pb + ver_size*2, ver_size);
    same += .6/3*uint8_cmp(pc, pc + ver_size, pc + ver_size*2, ver_size);
    return same;
}

/* global */
uint64_t gb_video_pkt_pts = AV_NOPTS_VALUE;


/**
 * Convert an error code into a text message.
 * @param error Error code to be converted
 * @return Corresponding error text (not thread-safe)
 */
static const char *get_error_text(const int error)
{
    static char error_buffer[255];
    av_strerror(error, error_buffer, sizeof(error_buffer));
    return error_buffer;
}

int get_frame_from_packet(AVCodecContext *pCodecCtx,
                      AVPacket       *pkt,
                      AVFrame        *pFrame)
{
    int fret;

    /// send packet for decoding
    fret = avcodec_send_packet(pCodecCtx, pkt);

    // ignore invalid packets and continue
    if(fret == AVERROR_INVALIDDATA ||
       fret == -1 /* Operation not permitted */
    )
        return AVERROR(EAGAIN);
    
    if (fret < 0) {
        av_log(NULL, AV_LOG_ERROR,  "Error sending a packet for decoding - %s\n", get_error_text(fret));
        exit(EXIT_ERROR);
    }

    fret = avcodec_receive_frame(pCodecCtx, pFrame);

    if (fret == AVERROR(EAGAIN))
        return fret;

    if(fret == AVERROR_EOF)
    {
        av_log(NULL, AV_LOG_ERROR, "No more frames: recieved AVERROR_EOF\n");
        return -1;
    }
    if (fret == AVERROR(EINVAL))
    {
        av_log(NULL, AV_LOG_ERROR, "Codec not opened: recieved AVERROR(EINVAL)\n");
        return -1;
    }
    if (fret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Error during decoding packet\n");
        exit(EXIT_ERROR);
    }
#if LIBAVUTIL_VERSION_INT >= AV_VERSION_INT(55, 34, 100)
    av_log(NULL, AV_LOG_VERBOSE, "Got picture from frame pts=%"PRId64"\n", pFrame->pts);
#else
    av_log(NULL, AV_LOG_VERBOSE, "Got picture, Frame pkt_pts=%"PRId64"\n", pFrame->pkt_pts);
#endif
    return 0;
}

/**
 * @brief read packet and decode it into a frame
 * @param pFormatCtx - input
 * @param pCodecCtx - input
 * @param pFrame - decoded video frame
 * @param video_index - input
 * @param pPts - on succes it is set to packet's pts
 * @return >0 if can read packet(s) & decode a frame
 *          0 if end of file
 *         <0 if error
 */
int
video_decode_next_frame(AVFormatContext *pFormatCtx,
       AVCodecContext  *pCodecCtx,
       AVFrame         *pFrame,     /* OUTPUT */
       int              video_index,
       int64_t         *pPts        /* OUTPUT */
       )
{
    assert(pFrame);
    assert(pPts);

    AVPacket*   pkt;
    AVStream*   pStream = pFormatCtx->streams[video_index];
    int         fret;       //function return code
    int         got_picture=0;
    uint64_t    pkt_without_pic=0;
    int         decoded_frame = 0;

    static int    run = 0;               // # of times read_and_decode has been called for a file
    static double avg_decoded_frame = 0; // average # of decoded frame

    pkt = av_packet_alloc();
    if (!pkt)
    {
        av_log(NULL, AV_LOG_ERROR ,"Could not allocate packet\n");
        return -1;
    }

    while(got_picture == 0)
    {
        /// read packet
        do
        {
            av_packet_unref(pkt);
            fret = av_read_frame(pFormatCtx, pkt);
            if(fret != 0)
            {
                av_log(NULL, AV_LOG_VERBOSE, "av_read_frame returned %d - considering as the end of file\n", fret);
                av_log(NULL, AV_LOG_ERROR, "Error reading from video file\n");
                return 0;
            }
        } while(pkt->stream_index != video_index);

        pkt_without_pic++;

        dump_packet(pkt, pStream);

        // Save global pts to be stored in pFrame in first call
        av_log(NULL, AV_LOG_VERBOSE, "*saving gb_video_pkt_pts: %"PRId64"\n", pkt->pts);
        gb_video_pkt_pts = pkt->pts;

        /// try to decode packet
        fret = get_frame_from_packet(pCodecCtx, pkt, pFrame);

        // need more video packet(s)
        if(fret == AVERROR(EAGAIN))
        {
            if(pkt_without_pic%50 == 0)
                av_log(NULL, AV_LOG_INFO, "  no picture in %"PRId64" packets\n", pkt_without_pic);

            if (pkt_without_pic >= MAX_PACKETS_WITHOUT_PICTURE) {
                av_log(NULL, AV_LOG_ERROR, "  * av_read_frame couldn't decode picture in %d packets\n", MAX_PACKETS_WITHOUT_PICTURE);
                av_packet_unref(pkt);
                av_packet_free(&pkt);
                return -1;
            }
            continue;
        }

        /// decoded frame
        if(fret == 0)
        {
            got_picture=1;
            pkt_without_pic=0;
            decoded_frame++;

            av_log(NULL, AV_LOG_VERBOSE, "*get_videoframe got frame: key_frame: %d, pict_type: %c\n", pFrame->key_frame, av_get_picture_type_char(pFrame->pict_type));

            if (0 == decoded_frame%200) {
                av_log(NULL, AV_LOG_INFO, "  picture not decoded in %d frames\n", decoded_frame);
            }
        }
        // error decoding packet
        else
        {
            av_packet_unref(pkt);
            av_packet_free(&pkt);
            return -1;
        }
    }  // end of while

    av_packet_unref(pkt);
    av_packet_free(&pkt);

    run++;
    avg_decoded_frame = (avg_decoded_frame*(run-1) + decoded_frame) / run;

    av_log(NULL, AV_LOG_VERBOSE, "*****got picture, repeat_pict: %d%s, key_frame: %d, pict_type: %c\n", pFrame->repeat_pict,
        (pFrame->repeat_pict > 0) ? "**r**" : "", pFrame->key_frame, av_get_picture_type_char(pFrame->pict_type));

    dump_stream(pStream);
    dump_codec_context(pCodecCtx);

    *pPts = gb_video_pkt_pts;
    return 1;
}


/* calculate timestamp to display to users
*/
double calc_time(int64_t timestamp, AVRational time_base, double start_time)
{
    // for files with start_time > 0, we need to subtract the start_time 
    // from timestamp. this should match the time display by MPC & VLC. 
    // however, for .vob files of dvds, after subtracting start_time
    // each file will start with timestamp 0 instead of continuing from the previous file.

    return av_rescale(timestamp, time_base.num, time_base.den) - start_time;
}

/*
return the duration. guess when unknown.
must be called after codec has been opened
*/
double guess_duration(AVFormatContext *pFormatCtx, int index, 
    AVCodecContext *pCodecCtx, AVFrame __attribute__((unused)) *pFrame)
{
    double duration = (double) pFormatCtx->duration / AV_TIME_BASE; // can be incorrect for .vob files
    if (duration > 0) {
        return duration;
    }

    AVStream *pStream = pFormatCtx->streams[index];
    double guess;

    // if stream bitrate is known we'll interpolate from file size.
    // pFormatCtx->start_time would be incorrect for .vob file with multiple titles.
    // pStream->start_time doesn't work either. so we'll need to disable timestamping.
    assert(NULL != pStream && NULL != pCodecCtx);

    int64_t file_size = avio_size(pFormatCtx->pb);

//    if (pStream->codec->bit_rate > 0 && file_size > 0) {
//        guess = 0.9 * file_size / (pStream->codec->bit_rate / 8);
    if (pCodecCtx->bit_rate > 0 && file_size > 0) {
        guess = 0.9 * file_size / (pCodecCtx->bit_rate / 8);
        if (guess > 0) {
            av_log(NULL, AV_LOG_ERROR, "  ** duration is unknown: %.2f; guessing: %.2f s from bit_rate\n", duration, guess);
            return guess;
        }
    }

    return -1;
    
    // the following doesn't work.
    /*
    // we'll guess the duration by seeking to near the end of the file and
    // decode a frame. the timestamp of that frame is the guess.
    // things get more complicated for dvd's .vob files. each .vob file
    // can contain more than 1 title. and each title will have its own pts.
    // for example, 90% of a .vob might be for title 1 and the last 10%
    // might be for title 2; seeking to near the end will end up getting 
    // title 2's pts. this problem cannot be solved if we just look at the
    // .vob files. need to process other info outside .vob files too.
    // as a result, the following will probably never work.
    // .vob files weirdness will make our assumption to seek by byte incorrect too.
    if (pFormatCtx->file_size <= 0) {
        return -1;
    }
    int64_t byte_pos = 0.9 * pFormatCtx->file_size;
    int ret = av_seek_frame(pFormatCtx, index, byte_pos, AVSEEK_FLAG_BYTE);
    if (ret < 0) { // failed
        return -1;
    }
    avcodec_flush_buffers(pCodecCtx);
    int64_t pts;
    ret = read_and_decode(pFormatCtx, index, pCodecCtx, pFrame, &pts, 0); // FIXME: key or not?
    if (ret <= 0) { // end of file or error
        av_log(NULL, AV_LOG_VERBOSE, "  read_and_decode during guessing duration failed\n");
        return -1;
    }
    double start_time = (double) pFormatCtx->start_time / AV_TIME_BASE; // FIXME: can be unknown?
    guess = calc_time(pts, pStream->time_base, start_time);
    if (guess <= 0) {
        return -1;
    }
    av_log(NULL, AV_LOG_ERROR, "  ** duration is unknown: %.2f; guessing: %.2f s.\n", duration, guess);

    // seek back to 0 & flush buffer; FIXME: is 0 correct?
    av_seek_frame(pFormatCtx, index, 0, AVSEEK_FLAG_BYTE); // ignore errors
    avcodec_flush_buffers(pCodecCtx);

    return guess;
    */
}

/*
try hard to seek
assume flags can be either 0 or AVSEEK_FLAG_BACKWARD
*/
int really_seek(AVFormatContext *pFormatCtx, int index, int64_t timestamp, int flags, double duration)
{
    assert(flags == 0 || flags == AVSEEK_FLAG_BACKWARD);
    int ret;

    /* first try av_seek_frame */
    ret = av_seek_frame(pFormatCtx, index, timestamp, flags);
    if (ret >= 0) { // success
        return ret;
    }

    /* then we try seeking to any (non key) frame AVSEEK_FLAG_ANY */
    ret = av_seek_frame(pFormatCtx, index, timestamp, flags | AVSEEK_FLAG_ANY);
    if (ret >= 0) { // success
        av_log(NULL, AV_LOG_INFO, "AVSEEK_FLAG_ANY: timestamp: %"PRId64"\n", timestamp); // DEBUG
        return ret;
    }

    /* and then we try seeking by byte (AVSEEK_FLAG_BYTE) */
    // here we assume that the whole file has duration seconds.
    // so we'll interpolate accordingly.
    AVStream *pStream = pFormatCtx->streams[index];
    double start_time = (double) pFormatCtx->start_time / AV_TIME_BASE; // in seconds
    // if start_time is negative, we ignore it; FIXME: is this ok?
    if (start_time < 0) {
        start_time = 0;
    }

    // normally when seeking by timestamp we add start_time to timestamp 
    // before seeking, but seeking by byte we need to subtract the added start_time
    timestamp -= start_time / av_q2d(pStream->time_base);
    int64_t file_size = avio_size(pFormatCtx->pb);
    if (file_size <= 0) {
        return -1;
    }
    if (duration > 0) {
        int64_t duration_tb = duration / av_q2d(pStream->time_base); // in time_base unit
        int64_t byte_pos = av_rescale(timestamp, file_size, duration_tb);
        av_log(NULL, AV_LOG_INFO, "AVSEEK_FLAG_BYTE: byte_pos: %"PRId64", timestamp: %"PRId64", file_size: %"PRId64", duration_tb: %"PRId64"\n", byte_pos, timestamp, file_size, duration_tb);
        return av_seek_frame(pFormatCtx, index, byte_pos, AVSEEK_FLAG_BYTE);
    }

    return -1;
}

/* 
modify name so that it'll (hopefully) be unique
by inserting a unique string before suffix.
if unum is != 0, it'll be used
returns the unique number
*/
int make_unique_name(char *name, char *suffix, int unum)
{
    // tmpnam() in mingw always return names which start with \ -- unuseable.
    // so we'll use random number instead.

    char unique[FILENAME_MAX];
    if (unum == 0) {
        unum = rand();
    }
    sprintf(unique, "_%d", unum);

    char *found = strlaststr(name, suffix);
    if (NULL == found || found == name) {
        strcat(name, unique); // this shouldn't happen
    } else {
        strcat(unique, found);
        strcpy(found, unique);
    }
    return unum;
}

/*
 * find first usable video stream (not cover art)
 * based on av_find_default_stream_index()
 * returns
 *      >0: video index
 *      -1: can't find any usable video
 */
int
find_default_videostream_index(AVFormatContext *s, int user_selected_video_stream)
{
    int default_stream_idx = -1;
    int cover_image;
    int n_video_stream = 0;
    unsigned int i;
    AVStream *st;

    for (i = 0; i < s->nb_streams; i++)
    {
        st = s->streams[i];
        if (st->codecpar->codec_type == AVMEDIA_TYPE_VIDEO)
        {
            cover_image = (st->disposition & AV_DISPOSITION_ATTACHED_PIC);

            if(user_selected_video_stream)
            {
                if (++n_video_stream == user_selected_video_stream)
                {
                    default_stream_idx = i;
                    av_log(NULL, AV_LOG_INFO, "Selecting video stream (-S): %d%s", user_selected_video_stream, NEWLINE);

                    if(cover_image)
                        av_log(NULL, AV_LOG_INFO, "  Warning: Selected video stream is \"cover art\"%s", NEWLINE);
                    break;
                }
            }
            else
            {
                if (!cover_image) {
                    default_stream_idx = i;
                    break;
                }
            }
        }
    }

    return default_stream_idx;
}

void rotate_geometry(int *w, int *h, int angle)
{
    if(abs(angle) == 90)
    {
        int tmp = *w;
        *w = *h;
        *h = tmp;
    }
}

gdImagePtr rotate_gdImage(gdImagePtr ip, int angle)
{
    if(angle == 0)
        return ip;
    
    int win = gdImageSX(ip);
    int hin = gdImageSY(ip);
    int wout = win;
    int hout = hin;

    if(abs(angle) == 90) {
        wout = hin;
        hout = win;
    }

    gdImagePtr ipr = gdImageCreateTrueColor(wout, hout);

    int i,j;

    for(i=0; i<win; i++)
        for(j=0; j<hin; j++)
            switch(angle)
            {
                case -180:
                case +180:
                    gdImageSetPixel(ipr, wout-i, hout-j, gdImageGetPixel(ip, i, j));
                    break;
                case   90:
                    gdImageSetPixel(ipr, j,      hout-i, gdImageGetPixel(ip, i, j));
                    break;
                case  -90:
                    gdImageSetPixel(ipr, wout-j, i,      gdImageGetPixel(ip, i, j));
                    break;
                default:
                    gdImageDestroy(ipr);
                    return ip;
            }
            
    gdImageDestroy(ip);
    return ipr;
}

/*
 * Find and extract album art / cover image
 */
void
save_cover_image(AVFormatContext *s, const char* cover_filename)
{
    int cover_stream_idx = -1;
    unsigned int i;

    // find first stream with cover art
    for (i = 0; i < s->nb_streams; i++)
    {
        if (s->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO &&
            (s->streams[i]->disposition & AV_DISPOSITION_ATTACHED_PIC))
        {
            cover_stream_idx  = (int)i;
            break;
        }
    }

    if(cover_stream_idx > -1)
    {
        AVPacket pkt = s->streams[cover_stream_idx]->attached_pic;

        if(pkt.data && pkt.size > 0)
        {
            av_log(NULL, AV_LOG_VERBOSE, "Found cover art in stream index %d.%s", cover_stream_idx, NEWLINE);

            FILE* image_file = fopen(cover_filename, "wb");
            if(image_file)
            {
                fwrite(pkt.data, pkt.size, 1, image_file);
                fclose(image_file);
            }
            else
                av_log(NULL, AV_LOG_ERROR, "Error opening file \"%s\" for writting!%s", cover_filename, NEWLINE);
        }
    }
    else
        av_log(NULL, AV_LOG_VERBOSE, "No cover art found.%s", NEWLINE);
}

void
calculate_thumnail(
        int req_step,
        int req_cols,
        int req_rows,
        int src_width,
        int src_height,
        int duration,
        thumbnail *tn
)
{

    tn->column = req_cols;

    if (req_step > 0)
        tn->step_t = req_step / tn->time_base;
    else
        tn->step_t = duration / tn->time_base / (tn->column * req_rows + 1);

    if (req_rows > 0) {
        tn->row = req_rows;
        // if # of columns is reduced, we should increase # of rows so # of tiles would be almost the same
        // could some users not want this?
    } else { // as many rows as needed
        tn->row = floor(duration / tn->column / (tn->step_t * tn->time_base) + 0.5); // round nearest
    }
    if (tn->row < 1) {
        tn->row = 1;
    }

    // make sure last row is full
    tn->step_t = duration / tn->time_base / (tn->column * tn->row + 1);

    int full_width = tn->column * (src_width + gb_g_gap) + gb_g_gap;
    if (gb_w_width > 0 && gb_w_width < full_width) {
        tn->img_width = gb_w_width;
    } else {
        tn->img_width = full_width;
    }
    tn->shot_width_out = floor((tn->img_width - gb_g_gap*(tn->column+1)) / (double)tn->column + 0.5); // round nearest
    tn->shot_width_out -= tn->shot_width_out%2; // floor to even number
    tn->shot_height_out = floor((double) src_height / src_width * tn->shot_width_out + 0.5); // round nearest
    tn->shot_height_out -= tn->shot_height_out%2; // floor to even number
    tn->center_gap = (tn->img_width - gb_g_gap*(tn->column+1) - tn->shot_width_out * tn->column) / 2.0;
}

void
reduce_shots_to_fit_in(
    int req_step,
    int req_rows,
    int req_cols,
    int src_width,
    int src_height,
    int duration,
    thumbnail *tn
)
{
    int reduced_columns = req_cols + 1;  // will be -1 in the loop

    tn->step_t = -99999;
    tn->column = -99999;
    tn->row = -99999;
    tn->img_width = -99999;
    tn->shot_width_out = -99999;
    tn->shot_height_out = -99999;

    // reduce # of columns to meet required height
    while (tn->shot_height_out < gb_h_height && reduced_columns > 0 && tn->shot_width_out != src_width) {
        reduced_columns--;

        calculate_thumnail(
            req_step,
            reduced_columns,
            req_rows,
            src_width,
            src_height,
            duration,
            tn
        );
    }

    // reduce # of rows if movie is too short
    if (tn->step_t <= 0 &&
        tn->column > 0 &&
        tn->row > 1)
    {
        int reduced_rows = (int)((double)(duration-1) /(double)reduced_columns);

        if(reduced_rows == 0)
            reduced_rows = 1;

        av_log(NULL, AV_LOG_INFO, "  movie is too short, reducing number of rows to %d%s", reduced_rows, NEWLINE);

        calculate_thumnail(
            req_step,
            reduced_columns,
            reduced_rows,
            src_width,
            src_height,
            duration,
            tn
        );
    }
}

/*
 * return   0 ok
 *         -1 something went wrong
 *          1 some images are missing
 */
int
make_thumbnail(char *file)
{
    int return_code = -1;
    av_log(NULL, AV_LOG_VERBOSE, "make_thumbnail: %s\n", file);
    static int nb_file = 0; // FIXME: static
    nb_file++;
    int idx = 0;
    int thumb_nb = 0;

    struct timeval tstart;
    gettimeofday(&tstart, NULL);

    thumbnail tn; // thumbnail data & info
    thumb_new(&tn);
    gdImagePtr thumbShadowIm=NULL;

    int nb_shots = 0; // # of decoded shots (stat purposes)

    /* these are checked during cleaning up, must be NULL if not used */
    AVFormatContext *pFormatCtx = NULL;
    AVCodecContext *pCodecCtx = NULL;
    AVFrame *pFrame = NULL;
    AVFrame *pFrameRGB = NULL;
    uint8_t *rgb_buffer = NULL;
    struct SwsContext *pSwsCtx = NULL;
    tn.out_ip = NULL;
    //FILE *out_fp = NULL;
    FILE *info_fp = NULL;
    gdImagePtr ip = NULL;

    int t_timestamp = gb_t_timestamp; // local timestamp; can be turned off; 0 = off
    int ret;

    av_log(NULL, AV_LOG_INFO, "\n");

    {
        char *extpos;
        char *filenamepos = NULL;
        char filenamebase[UTF8_FILENAME_SIZE] = {'\0',};

        if (gb_O_outdir != NULL && strlen(gb_O_outdir) > 0) {
            strcpy_va(filenamebase, 3, gb_O_outdir, "/", path_2_file(file));
        } else {
            strcpy(filenamebase, file);
        }

        filenamepos=path_2_file(filenamebase);
        extpos = strrchr(filenamepos, '.');

        if (gb_X_filename_use_full != 1 && extpos != NULL)
        {
            // remove movie extenxtion (e.g. .avi)
            *extpos = '\0';
        }

        strcpy(tn.out_filename, filenamebase);
        strcat(tn.out_filename, gb_o_suffix);

        if (gb_N_suffix != NULL)
        {
            strcpy(tn.info_filename, filenamebase);
            strcat(tn.info_filename, gb_N_suffix);
        }

        if (gb__cover == 1)
        {
            strcpy(tn.cover_filename, filenamebase);
            strcat(tn.cover_filename, gb__cover_suffix);
        }
    }

    char *suffix;

    // idenfity thumbnail image extension
    char image_extension[5];
    suffix = strrchr(tn.out_filename, '.');
    if(suffix && strcasecmp(suffix, ".png")==0 )
        strcpy(image_extension, IMAGE_EXTENSION_PNG);
    else
        strcpy(image_extension, IMAGE_EXTENSION_JPG);


    // if output files exist and modified time >= program start time,
    // we'll not overwrite and use a new name
    int unum = 0;
    if (is_reg_newer(tn.out_filename, gb_st_start)) {
        unum = make_unique_name(tn.out_filename, gb_o_suffix, unum);
        av_log(NULL, AV_LOG_INFO, "%s: output file already exists. using: %s\n", gb_argv0, tn.out_filename);
    }
    if (NULL != gb_N_suffix && is_reg_newer(tn.info_filename, gb_st_start)) {
        unum = make_unique_name(tn.info_filename, gb_N_suffix, unum);
        av_log(NULL, AV_LOG_INFO, "%s: info file already exists. using: %s\n", gb_argv0, tn.info_filename);
    }
    if (0 == gb_W_overwrite) { // dont overwrite mode
        if (is_reg(tn.out_filename)) {
            av_log(NULL, AV_LOG_INFO, "%s: output file %s already exists. omitted.\n", gb_argv0, tn.out_filename);
            return_code = 0;
            goto cleanup;
        }
        if (NULL != gb_N_suffix && is_reg(tn.info_filename)) {
            av_log(NULL, AV_LOG_INFO, "%s: info file %s already exists. omitted.\n", gb_argv0, tn.info_filename);
            return_code = 0;
            goto cleanup;
        }
    }
#if defined(WIN32) && defined(_UNICODE)
//    wchar_t out_filename_w[FILENAME_MAX];
//    UTF8_2_WC(out_filename_w, tn.out_filename, FILENAME_MAX);
    wchar_t info_filename_w[FILENAME_MAX];
    UTF8_2_WC(info_filename_w, tn.info_filename, FILENAME_MAX);
#else
//    char *out_filename_w = tn.out_filename;
    char *info_filename_w = tn.info_filename;
#endif
//    out_fp = _tfopen(out_filename_w, _TEXT("wb"));
//    if (NULL == out_fp) {
//        av_log(NULL, AV_LOG_ERROR, "\n%s: creating output image '%s' failed: %s\n", gb_argv0, tn.out_filename, strerror(errno));
//        goto cleanup;
//    }
    if (NULL != gb_N_suffix) {
        av_log(NULL, AV_LOG_INFO, "\nCreating info file %s\n", tn.info_filename);
        info_fp = _tfopen(info_filename_w, _TEXT("wb"));
        if (NULL == info_fp) {
            av_log(NULL, AV_LOG_ERROR, "\n%s: creating info file '%s' failed: %s\n", gb_argv0, tn.info_filename, strerror(errno));
            goto cleanup;
        }
    }

    // Open video file
    ret = avformat_open_input(&pFormatCtx, file, NULL, NULL);
    if (0 != ret) {
        av_log(NULL, AV_LOG_ERROR, "\n%s: avformat_open_input %s failed: %d\n", gb_argv0, file, ret);
        goto cleanup;
    }

    // generate pts?? -- from ffplay, not documented
    // it should make av_read_frame() generate pts for unknown value
    assert(NULL != pFormatCtx);
    pFormatCtx->flags |= AVFMT_FLAG_GENPTS;

    // Retrieve stream information
    ret = avformat_find_stream_info(pFormatCtx, NULL);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "\n%s: avformat_find_stream_info %s failed: %d\n", gb_argv0, file, ret);
        goto cleanup;
    }
    dump_format_context(pFormatCtx, nb_file, file, 0);

    // Find videostream
    int video_index = find_default_videostream_index(pFormatCtx, gb_S_select_video_stream);
    if (video_index == -1)
    {
        if(!gb_S_select_video_stream)
            av_log(NULL, AV_LOG_ERROR, "  couldn't find a video stream\n");
        else
            av_log(NULL, AV_LOG_ERROR, "  couldn't find selected video stream (-S %d)\n", gb_S_select_video_stream);
        goto cleanup;
    }

    AVStream *pStream = pFormatCtx->streams[video_index];
    pCodecCtx = get_codecContext_from_codecParams(pStream->codecpar);
    tn.time_base = av_q2d(pStream->time_base);

    if(!pCodecCtx)
        goto cleanup;

    if((tn.rotation = get_stream_rotation(pStream)) != 0)
        av_log(NULL, AV_LOG_INFO,  "  Rotation: %d degrees%s", tn.rotation, NEWLINE);
    
    dump_stream(pStream);
    //dump_index_entries(pStream);
    dump_codec_context(pCodecCtx);
    av_log(NULL, AV_LOG_VERBOSE, "\n");

    // Find the decoder for the video stream
    AVCodec *pCodec = avcodec_find_decoder(pCodecCtx->codec_id);
    if (pCodec == NULL) {
        av_log(NULL, AV_LOG_ERROR, "  couldn't find a decoder for codec_id: %d\n", pCodecCtx->codec_id);
        goto cleanup;
    }
//    const AVCodec *pCodec = pCodecCtx->codec;

    // discard frames; is this OK?? // FIXME
    if (gb_s_step >= 0) {
        // nonkey & bidir cause program crash with some files, e.g. tokyo 275 .
        // codec bugs???
        //pCodecCtx->skip_frame = AVDISCARD_NONKEY; // slower with nike 15-11-07
        //pCodecCtx->skip_frame = AVDISCARD_BIDIR; // this seems to speed things up
        pCodecCtx->skip_frame = AVDISCARD_NONREF; // internal err msg but not crash
    }

    // Open codec
    ret = avcodec_open2(pCodecCtx, pCodec, NULL);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "  couldn't open codec %s id %d: %d\n", pCodec->name, pCodec->id, ret);
        goto cleanup;
    }

    // Allocate video frame
    pFrame = av_frame_alloc();
    if (pFrame == NULL) {
        av_log(NULL, AV_LOG_ERROR, "  couldn't allocate a video frame\n");
        goto cleanup;
    }

    if( gb__cover )
        save_cover_image(pFormatCtx, tn.cover_filename);


    // keep a copy of sample_aspect_ratio because it might be changed after 
    // decoding a frame, e.g. Dragonball Z 001 (720x480 H264 AAC).mkv
    // is this a codec bug? it seem this value can be in the header or in the stream.
    AVRational sample_aspect_ratio = pCodecCtx->sample_aspect_ratio;

    double duration = (double) pFormatCtx->duration / AV_TIME_BASE; // can be unknown & can be incorrect (e.g. .vob files)
    if (duration <= 0) {
        duration = guess_duration(pFormatCtx, video_index, pCodecCtx, pFrame);
    }
    if (duration <= 0) {
        // have to turn timestamping off because it'll be incorrect
        if (1 == gb_t_timestamp) { // on
            t_timestamp = 0;
            av_log(NULL, AV_LOG_ERROR, "  turning time stamp off because of duration\n");
        }
        av_log(NULL, AV_LOG_ERROR, "  duration is unknown: %.2f\n", duration);
        goto cleanup;
    }

    double start_time = (double) pFormatCtx->start_time / AV_TIME_BASE; // in seconds
    // VTS_01_2.VOB & beyond from DVD seem to be like this
    //if (start_time > duration) {
        //av_log(NULL, AV_LOG_VERBOSE, "  start_time: %.2f is more than duration: %.2f\n", start_time, duration);
        //goto cleanup;
    //}
    // if start_time is negative, we ignore it; FIXME: is this ok?
    if (start_time < 0) {
        start_time = 0;
    }
    int64_t start_time_tb = start_time * pStream->time_base.den / pStream->time_base.num; // in time_base unit
    //av_log(NULL, AV_LOG_ERROR, "  start_time_tb: %"PRId64"\n", start_time_tb);

    // decode the first frame without seeking.
    // without doing this, avcodec_decode_video wont be able to decode any picture
    // with some files, eg. http://download.pocketmovies.net/movies/3d/twittwit_320x184.mpg
    // bug reported by: swmaherl, jake_o from sourceforge
    // and pCodecCtx->width and pCodecCtx->height might not be correct without this
    // for .flv files. bug reported by: dragonbook 
    int64_t found_pts = -1;
    int64_t first_pts = -1; // pts of first frame
    ret = video_decode_next_frame(pFormatCtx, pCodecCtx, pFrame, video_index, &first_pts);
    if (0 == ret) { // end of file
        goto eof;
    } else if (ret < 0) { // error
        av_log(NULL, AV_LOG_ERROR, "  read_and_decode first failed!\n");
        goto cleanup;
    }
    //av_log(NULL, AV_LOG_INFO, "first_pts: %"PRId64" (%.2f s)\n", first_pts, calc_time(first_pts, pStream->time_base, start_time)); // DEBUG

    // set sample_aspect_ratio
    // assuming sample_y = display_y
    if (gb_a_ratio.num != 0) { // use cmd line arg if specified
        sample_aspect_ratio.num = (double) pCodecCtx->height * av_q2d(gb_a_ratio) / pCodecCtx->width * 10000;
        sample_aspect_ratio.den = 10000;
        av_log(NULL, AV_LOG_INFO, "  *** using sample_aspect_ratio: %d/%d because of -a %.4f option\n", sample_aspect_ratio.num, sample_aspect_ratio.den, av_q2d(gb_a_ratio));
    } else {
        if (sample_aspect_ratio.num != 0 && pCodecCtx->sample_aspect_ratio.num != 0
            && av_q2d(sample_aspect_ratio) != av_q2d(pCodecCtx->sample_aspect_ratio)) {
            av_log(NULL, AV_LOG_INFO, "  *** conflicting sample_aspect_ratio: %.2f vs %.2f: using %.2f\n",
                av_q2d(sample_aspect_ratio), av_q2d(pCodecCtx->sample_aspect_ratio), av_q2d(sample_aspect_ratio));
            av_log(NULL, AV_LOG_INFO, "      to use sample_aspect_ratio %.2f use: -a %.4f option\n",
                av_q2d(pCodecCtx->sample_aspect_ratio), av_q2d(pCodecCtx->sample_aspect_ratio) * pCodecCtx->width / pCodecCtx->height);
            // we'll continue with existing value. is this ok? FIXME
            // this is the same as mpc's and vlc's. 
        }
        if (sample_aspect_ratio.num == 0) { // not defined
            sample_aspect_ratio = pCodecCtx->sample_aspect_ratio;
        }
    }

    /* calc options */
    // FIXME: make sure values are ok when movies are very short or very small
    double net_duration;
    if (gb_C_cut > 0) {
        net_duration = gb_C_cut;
        if (net_duration + gb_B_begin > duration) {
            net_duration = duration - gb_B_begin;
            av_log(NULL, AV_LOG_ERROR, "  -C %.2f s is too long, using %.2f s.\n", gb_C_cut, net_duration);
        }
    } else {
        //double net_duration = duration - start_time - gb_B_begin - gb_E_end;
        net_duration = duration - gb_B_begin - gb_E_end; // DVD
        if (net_duration <= 0) {
            av_log(NULL, AV_LOG_ERROR, "  duration: %.2f s, net duration after -B & -E is negative: %.2f s.\n", duration, net_duration);
            goto cleanup;
        }
    }

    /* scale according to sample_aspect_ratio. */
    int scaled_src_width, scaled_src_height;

    calc_scale_src(pCodecCtx->width, pCodecCtx->height, sample_aspect_ratio,
        &scaled_src_width, &scaled_src_height);

    if (scaled_src_width != pCodecCtx->width || scaled_src_height != pCodecCtx->height) {
        av_log(NULL, AV_LOG_INFO, "  * scaling input * %dx%d => %dx%d according to sample_aspect_ratio %d/%d\n",
            pCodecCtx->width, pCodecCtx->height, scaled_src_width, scaled_src_height, 
            sample_aspect_ratio.num, sample_aspect_ratio.den);
    }

    int seek_mode = 1; // 1 = seek; 0 = non-seek
    int scaled_src_width_out  = scaled_src_width,
        scaled_src_height_out = scaled_src_height;

    rotate_geometry(&scaled_src_width_out, &scaled_src_height_out, tn.rotation);

    reduce_shots_to_fit_in(
        gb_s_step,
        gb_r_row,
        gb_c_column,
        scaled_src_width_out,
        scaled_src_height_out,
        net_duration,
        &tn
    );

    if(tn.column == 0)
    {
        int suggested_width, suggested_height;
        // guess new width and height to create thumbnails
        suggested_width = ceil(gb_h_height * scaled_src_width_out/scaled_src_height_out + 2*(double)gb_g_gap);
        suggested_width+= suggested_width%2;
        suggested_height = floor((gb_w_width - 2*gb_g_gap) * scaled_src_height_out/scaled_src_width_out);
        suggested_height-= suggested_height%2;

        av_log(NULL, AV_LOG_ERROR, "  thumbnail to small; increase image width to %d (-w) or decrease min. image height to %d (-h)%s" ,
               suggested_width, suggested_height, NEWLINE);
        goto cleanup;
    }

    if (tn.step_t == 0) {
        av_log(NULL, AV_LOG_ERROR, "  step is zero; movie is too short?\n");
        goto cleanup;
    }

    if(abs(tn.rotation) == 90){
        tn.shot_height_in = tn.shot_width_out;
        tn.shot_width_in  = tn.shot_height_out;
    } else {
        tn.shot_height_in = tn.shot_height_out;
        tn.shot_width_in  = tn.shot_width_out;
    }

    if (tn.column != gb_c_column) {
        av_log(NULL, AV_LOG_INFO, "  changing # of column to %d to meet minimum height of %d; see -h option\n", tn.column, gb_h_height);
    }
    if (gb_w_width > 0 && gb_w_width != tn.img_width) {
        av_log(NULL, AV_LOG_INFO, "  changing width to %d to match movie's size (%dx%d)\n", tn.img_width, scaled_src_width, tn.column);
    }
    char *all_text = get_stream_info(pFormatCtx, file, 1, sample_aspect_ratio); // FIXME: using function's static buffer
    if (NULL != info_fp) {
        fprintf(info_fp, "%s%s", all_text, NEWLINE);
    }
    if (0 == gb_i_info) { // off
        *all_text = '\0';
    }
    if (NULL != gb_T_text) {
        sprintf(all_text+strlen(all_text), "%s%s", NEWLINE, gb_T_text);
        if (NULL != info_fp) {
            fprintf(info_fp, "%s%s", gb_T_text, NEWLINE);
        }
    }
    if(gb_i_info == 1)
        tn.txt_height = image_string_height(all_text, gb_f_fontname, gb_F_info_font_size) + gb_g_gap;
    tn.img_height = tn.shot_height_out*tn.row + gb_g_gap*(tn.row+1) + tn.txt_height;
    av_log(NULL, AV_LOG_INFO, "  step: %.1f s; # tiles: %dx%d, tile size: %dx%d; total size: %dx%d\n",
        tn.step_t*tn.time_base, tn.column, tn.row, tn.shot_width_out, tn.shot_height_out, tn.img_width, tn.img_height);

    // jpeg seems to have max size of 65500 pixels
    if (strcasecmp(image_extension, IMAGE_EXTENSION_JPG)==0 && (tn.img_width > 65500 || tn.img_height > 65500)) {
        av_log(NULL, AV_LOG_ERROR, "  jpeg only supports max size of 65500\n");
        goto cleanup;
    }

    int64_t evade_step = MIN(10/tn.time_base, tn.step_t / 14); // max 10 s to evade blank screen
    if (evade_step*tn.time_base <= 1) {
        evade_step = 0;
        av_log(NULL, AV_LOG_INFO, "  step is less than 14 s; blank & blur evasion is turned off.\n");
    }

    /* prepare for resize & conversion to AV_PIX_FMT_RGB24 */
    pFrameRGB = av_frame_alloc();
    if (pFrameRGB == NULL) {
        av_log(NULL, AV_LOG_ERROR, "  couldn't allocate a video frame\n");
        goto cleanup;
    }
    int rgb_bufsize = av_image_get_buffer_size(AV_PIX_FMT_RGB24, tn.shot_width_in, tn.shot_height_in, LINESIZE_ALIGN);
    rgb_buffer = av_malloc(rgb_bufsize);
//    rgb_buffer = (uint8_t*)malloc(rgb_bufsize*sizeof(uint8_t));

    if (NULL == rgb_buffer) {
        av_log(NULL, AV_LOG_ERROR, "  av_malloc %d bytes failed\n", rgb_bufsize);
        goto cleanup;
    }
    // Returns: the size in bytes required for src, a negative error code in case of failure
    ret = av_image_fill_arrays(pFrameRGB->data, pFrameRGB->linesize, rgb_buffer, AV_PIX_FMT_RGB24, tn.shot_width_in, tn.shot_height_in, LINESIZE_ALIGN);
    if(ret <0 )
    {
        av_log(NULL, AV_LOG_ERROR, "  av_image_fill_arrays failed (%d)\n", ret);
        goto cleanup;
    }

    pSwsCtx = sws_getContext(pCodecCtx->width, pCodecCtx->height, pCodecCtx->pix_fmt,
        tn.shot_width_in, tn.shot_height_in, AV_PIX_FMT_RGB24, SWS_BILINEAR, NULL, NULL, NULL);
    if (NULL == pSwsCtx) { // sws_getContext is not documented
        av_log(NULL, AV_LOG_ERROR, "  sws_getContext failed\n");
        goto cleanup;
    }

    /* create the output image */
    tn.out_ip = gdImageCreateTrueColor(tn.img_width, tn.img_height);
    if (NULL == tn.out_ip) {
        av_log(NULL, AV_LOG_ERROR, "  gdImageCreateTrueColor failed: width %d, height %d\n", tn.img_width, tn.img_height);
        goto cleanup;
    }

    
    /* setting alpha blending is not needed, using default mode:
     * https://libgd.github.io/manuals/2.2.5/files/gd-h.html#Effects
    gdImageAlphaBlending(tn.out_ip,	
		//gdEffectReplace		//replace pixels
		gdEffectAlphaBlend	   	//blend pixels, see gdAlphaBlend
		//gdEffectNormal		//default mode; same as gdEffectAlphaBlend
		//gdEffectOverlay		//overlay pixels, see gdLayerOverlay
		//gdEffectMultiply	//overlay pixels with multiply effect, see gdLayerMultiply
    );
    */
    int background = gdImageColorResolve(tn.out_ip, gb_k_bcolor.r, gb_k_bcolor.g, gb_k_bcolor.b); // set backgroud
    gdImageFilledRectangle(tn.out_ip, 0, 0, tn.img_width, tn.img_height, background);
    
    if(gb__transparent_bg)
		gdImageColorTransparent (tn.out_ip, background);

    /* add info & text */ // do this early so when font is not found we'll quit early
    if (NULL != all_text && strlen(all_text) > 0) {
        char *str_ret = image_string(tn.out_ip, 
            gb_f_fontname, gb_F_info_color, gb_F_info_font_size, 
            gb_L_info_location, gb_g_gap, all_text, 0, COLOR_WHITE);
        if (NULL != str_ret) {
            av_log(NULL, AV_LOG_ERROR, "  %s; font problem? see -f option\n", str_ret);
            goto cleanup;
        }
    }

	/* if needed create shadow image used for every shot	*/
	if(gb__shadow >= 0){
		if((thumbShadowIm = create_shadow_image(background, &gb__shadow, tn.shot_width_out, tn.shot_height_out)) == NULL)
			goto cleanup;
	}

    /* alloc dynamic thumb data */
    if (-1 == thumb_alloc_dynamic(&tn)) {
        av_log(NULL, AV_LOG_ERROR, "  thumb_alloc_dynamic failed\n");
        goto cleanup;
    }

    if (1 == gb_z_seek) {
        seek_mode = 1;
    }
    if (1 == gb_Z_nonseek) {
        seek_mode = 0;
        av_log(NULL, AV_LOG_INFO, "  *** using non-seek mode -- slower but more accurate timing.\n");
    }

    int64_t seek_target, seek_evade; // in time_base unit

    /* decode & fill in the shots */
  restart:
    seek_target = 0, seek_evade = 0; // in time_base unit
    if (0 == seek_mode && gb_B_begin > 10) {
        av_log(NULL, AV_LOG_INFO, "  -B %.2f with non-seek mode will take some time.\n", gb_B_begin);
    }

    int evade_try = 0; // blank screen evasion index
    double avg_evade_try = 0; // average
    int direction = 0; // seek direction (seek flags)
    seek_target = tn.step_t + (start_time + gb_B_begin) / tn.time_base;
    idx = 0; // idx = thumb_idx
    thumb_nb = tn.row * tn.column; // thumb_nb = # of shots we need
    int64_t prevshot_pts = -1; // pts of previous good shot
    int64_t prevfound_pts = -1; // pts of previous decoding
    gdImagePtr edge_ip = NULL; // edge image

    for (idx = 0; idx < thumb_nb; idx++) {

        int64_t eff_target = seek_target + seek_evade; // effective target
        eff_target = MAX(eff_target, start_time_tb); // make sure eff_target > start_time
        TIME_STR time_tmp;
        format_time(calc_time(eff_target, pStream->time_base, start_time), time_tmp, ':');

        /* for some formats, previous seek might over shoot pass this seek_target; is this a bug in libavcodec? */
        if (prevshot_pts > eff_target && 0 == evade_try) {
            // restart in seek mode of skipping shots (FIXME)
            if ( seek_mode == 1 && 0 == gb_z_seek ) {
              av_log(NULL, AV_LOG_INFO, "  *** previous seek overshot target %s; switching to non-seek mode\n", time_tmp);
              av_seek_frame(pFormatCtx, video_index, 0, 0);
              avcodec_flush_buffers(pCodecCtx);
              seek_mode = 0;
              goto restart;
            }
            av_log(NULL, AV_LOG_INFO, "  skipping shot at %s because of previous seek or evasions\n", time_tmp);
            idx--;
            thumb_nb--;
            goto skip_shot;
        }

        // make sure eff_target > previous found
        eff_target = MAX(eff_target, prevfound_pts+1);

        format_time(calc_time(eff_target, pStream->time_base, start_time), time_tmp, ':');
        av_log(NULL, AV_LOG_VERBOSE, "\n***eff_target tb: %"PRId64", eff_target s:%.2f (%s), prevshot_pts: %"PRId64"\n", 
            eff_target, calc_time(eff_target, pStream->time_base, start_time), time_tmp, prevshot_pts);

        /* jump to next shot */
        //struct timeval dstart; // DEBUG
        //gettimeofday(&dstart, NULL); // calendar time; effected by load & io & etc. DEBUG
        if (1 == seek_mode) { // seek mode
            ret = really_seek(pFormatCtx, video_index, eff_target, direction, duration);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "  seeking to %.2f s failed\n", calc_time(eff_target, pStream->time_base, start_time));
                goto cleanup;
            }
            avcodec_flush_buffers(pCodecCtx);

            ret = video_decode_next_frame(pFormatCtx, pCodecCtx, pFrame, video_index, &found_pts);
            if (0 == ret) { // end of file
                goto eof;
            } else if (ret < 0) { // error
                av_log(NULL, AV_LOG_ERROR, "  read&decode failed!\n");
                goto cleanup;
            }
        } else { // non-seek mode -- we keep decoding until we get to the next shot
            found_pts = 0;
            while (found_pts < eff_target) {
                // we should check if it's taking too long for this loop. FIXME
                ret =  video_decode_next_frame(pFormatCtx, pCodecCtx, pFrame, video_index, &found_pts);
                if (0 == ret) { // end of file
                    goto eof;
                } else if (ret < 0) { // error
                    av_log(NULL, AV_LOG_ERROR, "  read&decode failed!\n");
                    goto cleanup;
                }
            }
        }
        //struct timeval dfinish; // DEBUG
        //gettimeofday(&dfinish, NULL); // calendar time; effected by load & io & etc. DEBUG
        //double decode_time = (dfinish.tv_sec + dfinish.tv_usec/1000000.0) - (dstart.tv_sec + dstart.tv_usec/1000000.0);
        double decode_time = 0;

        int64_t found_diff = found_pts - eff_target;
        //av_log(NULL, AV_LOG_INFO, "  found_diff: %.2f\n", found_diff); // DEBUG
        // if found frame is too far off from target, we'll disable seeking and start over
        if (idx < 5 && 1 == seek_mode && 0 == gb_z_seek 
            // usually movies have key frames every 10 s
            && (tn.step_t < (15/tn.time_base) || found_diff > 15/tn.time_base)
            && (found_diff <= -tn.step_t || found_diff >= tn.step_t)) {
            
            // compute the approx. time it take for the non-seek mode, if too long print a msg instead
            double shot_dtime;
            if (scaled_src_width > 576*4/3.0) { // HD
                shot_dtime = tn.step_t*tn.time_base * 30 / 30.0;
            } else if (scaled_src_width > 288*4/3.0) { // ~DVD
                shot_dtime = tn.step_t*tn.time_base * 30 / 80.0;
            } else { // small
                shot_dtime = tn.step_t*tn.time_base * 30 / 500.0;
            }
            if (shot_dtime > 2 || shot_dtime * tn.column * tn.row > 120) {
                av_log(NULL, AV_LOG_INFO, "  *** seeking off target %.2f s, increase time step or use non-seek mode.\n", found_diff*tn.time_base);
                goto non_seek_too_long;
            }

            // disable seeking and start over
            av_seek_frame(pFormatCtx, video_index, 0, 0);
            avcodec_flush_buffers(pCodecCtx);
            seek_mode = 0;
            av_log(NULL, AV_LOG_INFO, "  *** switching to non-seek mode because seeking was off target by %.2f s.\n", found_diff*tn.time_base);
            av_log(NULL, AV_LOG_INFO, "  non-seek mode is slower. increase time step or use -z if you don't want this.\n");
            goto restart;
        }
      non_seek_too_long:

        nb_shots++;
        av_log(NULL, AV_LOG_VERBOSE, "shot %d: found_: %"PRId64" (%.2fs), eff_: %"PRId64" (%.2fs), dtime: %.3f\n", 
            idx, found_pts, calc_time(found_pts, pStream->time_base, start_time), 
            eff_target, calc_time(eff_target, pStream->time_base, start_time), decode_time);
        av_log(NULL, AV_LOG_VERBOSE, "approx. decoded frames/s: %.2f\n", tn.step_t * tn.time_base * 30 / decode_time); //TODO W: decode_time allways==0
        /*
        char debug_filename[2048]; // DEBUG
        sprintf(debug_filename, "%s_decoded%05d.jpg", tn.out_filename, nb_shots - 1);
        save_AVFrame(pFrame, pCodecCtx->width, pCodecCtx->height, pCodecCtx->pix_fmt, 
            debug_filename, pCodecCtx->width, pCodecCtx->height);
        */

        // got same picture as previous shot, we'll skip it
        if (prevshot_pts == found_pts && 0 == evade_try) {
            av_log(NULL, AV_LOG_INFO, "  skipping shot at %s because got previous shot\n", time_tmp);
            idx--;
            thumb_nb--;
            goto skip_shot;
        }

        /* convert to AV_PIX_FMT_RGB24 & resize */
        int output_height; //the height of the output slice
        output_height = sws_scale(pSwsCtx, (const uint8_t* const*)pFrame->data, pFrame->linesize, 0, pCodecCtx->height,
            pFrameRGB->data, pFrameRGB->linesize);
        if(output_height <= 0)
        {
            av_log(NULL, AV_LOG_ERROR, "  sws_scale() failed\n");
            goto cleanup;
        }
        /*
        sprintf(debug_filename, "%s_resized%05d.jpg", tn.out_filename, nb_shots - 1); // DEBUG
        save_AVFrame(pFrameRGB, tn.shot_width, tn.shot_height, AV_PIX_FMT_RGB24,
            debug_filename, tn.shot_width, tn.shot_height);
        */

        /* if blank screen, try again */
        // FIXME: make sure this'll work when step is small
        // FIXME: make sure each shot wont get repeated
        double blank = blank_frame(pFrameRGB, tn.shot_width_out, tn.shot_height_out);
        // only do edge when blank detection doesn't work
        float edge[EDGE_PARTS] = {1,1,1,1,1,1}; // FIXME: change this if EDGE_PARTS is changed
        if (evade_step > 0 && blank <= gb_b_blank && gb_D_edge > 0) {
            edge_ip = rotate_gdImage(
                detect_edge(pFrameRGB, &tn, edge, EDGE_FOUND),
                tn.rotation);

        }
        //av_log(NULL, AV_LOG_VERBOSE, "  idx: %d, evade_try: %d, blank: %.2f%s edge: %.3f %.3f %.3f %.3f %.3f %.3f%s\n", 
        //    idx, evade_try, blank, (blank > gb_b_blank) ? "**b**" : "", 
        //    edge[0], edge[1], edge[2], edge[3], edge[4], edge[5], is_edge(edge, EDGE_FOUND) ? "" : "**e**"); // DEBUG
        if (evade_step > 0 && (blank > gb_b_blank || !is_edge(edge, EDGE_FOUND))) {
            idx--;
            evade_try++;
            // we'll always search forward to support non-seek mode, which cant go backward
            // keep trying until getting close to next step
            seek_evade = evade_step * evade_try;
            if (seek_evade < (tn.step_t - evade_step)) {
                av_log(NULL, AV_LOG_VERBOSE, "  * blank or no edge * try #%d: seeking forward seek_evade: %"PRId64" (%.2f s)\n", 
                    evade_try, seek_evade, seek_evade * av_q2d(pStream->time_base));
                goto continue_cleanup;
            }

            // not found -- skip shot
            TIME_STR time_tmp;
            format_time(calc_time(seek_target, pStream->time_base, start_time), time_tmp, ':');
            av_log(NULL, AV_LOG_INFO, "  * blank %.2f or no edge * skipping shot at %s after %d tries\n", blank, time_tmp, evade_try);
            thumb_nb--; // reduce # shots
            goto skip_shot;
        }

        //
        avg_evade_try = (avg_evade_try * idx + evade_try ) / (idx+1); // DEBUG
        //av_log(NULL, AV_LOG_VERBOSE, "  *** avg_evade_try: %.2f\n", avg_evade_try); // DEBUG

        /* convert to GD image */
        ip = gdImageCreateTrueColor(tn.shot_width_in, tn.shot_height_in);
        if (NULL == ip) {
            av_log(NULL, AV_LOG_ERROR, "  gdImageCreateTrueColor failed: width %d, height %d\n", tn.shot_width_in, tn.shot_height_in);
            goto cleanup;
        }
        FrameRGB_2_gdImage(pFrameRGB, ip, tn.shot_width_in, tn.shot_height_in);
        ip = rotate_gdImage(ip, tn.rotation);

        /* if debugging, save the edge instead */
        if (gb_v_verbose > 0 && NULL != edge_ip) {
            gdImageDestroy(ip);
            ip = edge_ip;
            edge_ip = NULL;
        }

        /* timestamping */
        // FIXME: this frame might not actually be at the requested position. is pts correct?
        if (1 == t_timestamp) { // on
            TIME_STR time_str;
            format_time(calc_time(found_pts, pStream->time_base, start_time), time_str, ':');
            char *str_ret = image_string(ip, 
                gb_F_ts_fontname, gb_F_ts_color, gb_F_ts_font_size, 
                gb_L_time_location, 0, time_str, 1, gb_F_ts_shadow);
            if (NULL != str_ret) {
                av_log(NULL, AV_LOG_ERROR, "  %s; font problem? see -f option or -F option\n", str_ret);
                goto cleanup; // LEAK: ip, edge_ip
            }
            /* stamp idx & blank & edge for debugging */
            if (gb_v_verbose > 0) {
                char idx_str[1000]; // FIXME
                sprintf(idx_str, "idx: %d, blank: %.2f\n%.6f  %.6f\n%.6f  %.6f\n%.6f  %.6f", 
                    idx, blank, edge[0], edge[1], edge[2], edge[3], edge[4], edge[5]);
                image_string(ip, gb_f_fontname, COLOR_WHITE, gb_F_ts_font_size, 2, 0, idx_str, 1, COLOR_BLACK);
            }
        }

        /* save individual shots */
        if (1 == gb_I_individual) {
            TIME_STR time_str;
            format_time(calc_time(found_pts, pStream->time_base, start_time), time_str, '_');
            char individual_filename[UTF8_FILENAME_SIZE]; // FIXME
            strcpy(individual_filename, tn.out_filename);
            char *suffix = strstr(individual_filename, gb_o_suffix);
            assert(NULL != suffix);
            sprintf(suffix, "_%s_%05d%s", time_str, idx, image_extension);
            ret = save_image(ip, individual_filename);
            if (0 != ret) { // error
                av_log(NULL, AV_LOG_ERROR, "  saving individual shot #%05d to %s failed\n", idx, individual_filename);
            }
        }

        /* add picture to output image */
        thumb_add_shot(&tn, ip, thumbShadowIm, idx, found_pts);
        gdImageDestroy(ip);
        ip = NULL;

      skip_shot:
        /* step */
        seek_target += tn.step_t;
        
        seek_evade = 0;
        direction = 0;
        evade_try = 0;
        prevshot_pts = found_pts;
        av_log(NULL, AV_LOG_VERBOSE, "found_pts bottom: %"PRId64"\n", found_pts);
    
      continue_cleanup: // cleaning up before continuing the loop
        prevfound_pts = found_pts;
        if (NULL != edge_ip) {
            gdImageDestroy(edge_ip);
            edge_ip = NULL;
        }
    }
    av_log(NULL, AV_LOG_VERBOSE, "  *** avg_evade_try: %.2f\n", avg_evade_try); // DEBUG

  eof: ;
    /* crop if we dont get enough shots */
    int cropp_needed = 0;
    const int created_rows = ceil((double)idx / tn.column);
    int skipped_rows = tn.row - created_rows;
    if (skipped_rows == tn.row) {
        av_log(NULL, AV_LOG_ERROR, "  all rows're skipped?\n");
        goto cleanup;
    }
    if (0 != skipped_rows) {
        int cropped_height = tn.img_height - skipped_rows*tn.shot_height_out;

		tn.img_height = cropped_height;
		tn.row = created_rows;
		cropp_needed = 1;
    }

	if(created_rows == 1)
	{
		const int created_cols = idx;

		if(created_cols < tn.column)
		{
			int cropped_width = tn.img_width - (tn.column-created_cols)*tn.shot_width_out;

            tn.img_width = cropped_width;
            tn.column = created_cols;
            cropp_needed = 1;
		}
	}

	if(cropp_needed == 1)
	{
		tn.out_ip = crop_image(tn.out_ip, tn.img_width, tn.img_height);

		av_log(NULL, AV_LOG_INFO, "  changing # of tiles to %dx%d because of skipped shots; total size: %dx%d\n", 
			tn.column,
			tn.row,
			tn.img_width,
			tn.img_height
		);
	}

    /* save output image */
    if(save_image(tn.out_ip, tn.out_filename) == 0)
        tn.out_saved  = 1;
    else
        goto cleanup;

    struct timeval tfinish;
    gettimeofday(&tfinish, NULL); // calendar time; effected by load & io & etc.
    double diff_time = (tfinish.tv_sec + tfinish.tv_usec/1000000.0) - (tstart.tv_sec + tstart.tv_usec/1000000.0);
    // previous version reported # of decoded shots/s; now we report the # of final shots/s
    //av_log(NULL, AV_LOG_INFO, "  avg. %.2f shots/s; output file: %s\n", nb_shots / diff_time, tn.out_filename);
    av_log(NULL, AV_LOG_INFO, "  %.2f s, %.2f shots/s; output: %s\n",
        diff_time, (tn.idx + 1) / diff_time, tn.out_filename);

    if(tn.tiles_nr == (tn.row * tn.column))
        return_code = 0;        // everything is fine
    else
        return_code = 1;        // warning - some images are missing

  cleanup:
    if (NULL != ip)
        gdImageDestroy(ip);
    if (NULL != thumbShadowIm)
        gdImageDestroy(thumbShadowIm);
    if (NULL != tn.out_ip)
        gdImageDestroy(tn.out_ip);

    if (NULL != info_fp) {
        fclose(info_fp);
        if (1 != tn.out_saved) {
            _tunlink(info_filename_w);
        }
    }

    if (NULL != pSwsCtx)
        sws_freeContext(pSwsCtx); // do we need to do this?

    // Free the video frame
    if (NULL != rgb_buffer)
        av_free(rgb_buffer);
    if (NULL != pFrameRGB)
        av_free(pFrameRGB);
    if (NULL != pFrame)
        av_free(pFrame);

    // Close the codec
    if (NULL != pCodecCtx) {
        avcodec_close(pCodecCtx);
        avcodec_free_context(&pCodecCtx);
    }    

    // Close the video file
    if (NULL != pFormatCtx)
        avformat_close_input(&pFormatCtx);

    thumb_cleanup_dynamic(&tn);
    
    av_log(NULL, AV_LOG_VERBOSE, "make_thumbnail: done\n");
    return return_code;
}

/* modified from glibc
*/
int myalphasort(const void *a, const void *b)
{
    return strcoll(*(const char **) a, *(const char **) b);
}

/* modified from glibc
*/
int myalphacasesort(const void *a, const void *b)
{
    return strcasecmp(*(const char **) a, *(const char **) b);
}

/*
return 1 if filename has one of the predefined extensions
*/
int check_extension(char *filename)
{
    static char *movie_ext[] = {
        "3gp", "3g2", "asf", "avi", "avs", "dat", "divx", "dsm", "evo", "flv", 
        "m1v", "m2ts", "m2v", "m4a", "mj2", "mjpg", "mjpeg", "mkv", "mov", 
        "moov", "mp4", "mpg", "mpeg", "mpv", "nut", "ogg", "ogm", "qt", "rm", 
        "rmvb", "swf", "ts", "vob", "webm", "wmv", "xvid"
    }; // FIXME: static
    static int sorted = 0; // 1 = sorted

    static const int nb_ext = sizeof(movie_ext) / sizeof(*movie_ext);
    if (0 == sorted) {
        qsort(movie_ext, nb_ext, sizeof(*movie_ext), myalphacasesort);
        sorted = 1;
    }

    char *ext = strrchr(filename, '.');
    if (NULL == ext) {
        return 0;
    }
    ext += 1;
    if (NULL == bsearch(&ext, movie_ext, nb_ext, sizeof(*movie_ext), myalphacasesort)) {
        return 0;
    }
    if (NULL != strstr(filename, "uTorrentPartFile")) {
        return 0;
    }
    return 1;
}

int process_loop(int n, char **files, int current_depth);

/**
 * @brief modified from glibc's scandir -- mingw doesn't have scandir
 * @return 0- success, otherwise - failed
 */
int process_dir(char *dir, int current_depth)
{
    int return_code = -1;

    if(gb_d_depth >= 0 && current_depth>gb_d_depth)
        return 0;

    current_depth++;

#if defined(WIN32) && defined(_UNICODE)
    wchar_t dir_w[FILENAME_MAX];
    UTF8_2_WC(dir_w, dir, FILENAME_MAX);
#else
    char *dir_w = dir;
#endif

    _TDIR *dp = _topendir(dir_w);
    if (NULL == dp) {
        av_log(NULL, AV_LOG_ERROR, "\n%s: opendir failed: %s\n", dir, strerror(errno));
        return -1;
    }

    /* read directory & sort */
    struct _tdirent *d;
    char **v = NULL;
    size_t cnt = 0, vsize = 0;
    while (1) {
        errno = 0;
        d = _treaddir(dp);
        if (NULL == d) {
            if (0 != errno) { // is this check good?
                av_log(NULL, AV_LOG_ERROR, "\n%s: readdir failed: %s\n", dir, strerror(errno));
                goto cleanup;
            }
            break;
        }

        if (_tcscmp(d->d_name, _TEXT(".")) == 0 || _tcscmp(d->d_name, _TEXT("..")) == 0) {
            continue;
        }

#if defined(WIN32) && defined(_UNICODE)
        char d_name_utf8[UTF8_FILENAME_SIZE];
        WC_2_UTF8(d_name_utf8, d->d_name, UTF8_FILENAME_SIZE);
#else
        char *d_name_utf8 = d->d_name;
#endif

        char child_utf8[UTF8_FILENAME_SIZE];
        strcpy_va(child_utf8, 3, dir, "/", d_name_utf8);

        if (1 != is_dir(child_utf8) && 1 != check_extension(child_utf8)) {
            continue;
        }

        if (cnt == vsize) {
            char **new;
            if (vsize == 0)
                vsize = 50;
            else
                vsize *= 2;
            new = realloc(v, vsize * sizeof(*v));
            if (new == NULL) {
                // mingw doesn't seem to set errno for memory functions
                av_log(NULL, AV_LOG_ERROR, "\n%s: realloc failed: %s\n", dir, strerror(errno));
                goto cleanup;
            }
            v = new;
        }

        char *vnew = malloc(strlen(child_utf8) + 1); // for '\0'
        if (vnew == NULL) {
            av_log(NULL, AV_LOG_ERROR, "\n%s: malloc failed: %s\n", dir, strerror(errno));
            goto cleanup;
        }
        strcpy(vnew, child_utf8);
        v[cnt++] = vnew;
        //av_log(NULL, AV_LOG_INFO, "process_dir added: %s\n", v[cnt-1]); // DEBUG
    }
    qsort(v, cnt, sizeof(*v), myalphasort);

    /* process dirs & files */
    return_code = process_loop(cnt, v, current_depth);

  cleanup:
    while (cnt > 0)
        free(v[--cnt]);
    free(v);
    _tclosedir(dp);

    return return_code;
}

/**
 * @return
 *  0- success
 *  1- uncomplete image(s)
 *  2- error
 */
int process_loop(int n, char **files, int current_depth)
{
    int i;
    int files_done=0;
    int files_uncomplete=0;

    for (i = 0; i < n; i++) {
        av_log(NULL, AV_LOG_VERBOSE, "process_loop: %s\n", files[i]);
        rem_trailing_slash(files[i]); //

        if (is_dir(files[i])) { // directory
            //av_log(NULL, AV_LOG_INFO, "process_loop: %s is a DIR\n", files[i]); // DEBUG
            if(process_dir(files[i], current_depth) == 0)
                files_done++;
        } else { // not a directory

            switch (make_thumbnail(files[i])) {
            case 0:
                files_done++;
                break;
            case 1:
                files_done++;
                files_uncomplete++;
                break;
            default:
                break;
            }
        }
    }

    if(files_done == n && files_uncomplete > 0)
        return EXIT_WARNING;

    if(files_done == n)
        return EXIT_SUCCESS;

    return EXIT_ERROR;
}

// copied & modified from mingw-runtime-3.13's init.c
typedef struct STARTUPINFO{
  int newmode;
} _startupinfo;
extern void __wgetmainargs (int *, wchar_t ***, wchar_t ***, int, _startupinfo *);

char *gb_argv[10240]; // FIXME: global & hopefully noone will use more than this
/*
get command line arguments and expand wildcards in utf-8 in windows
caller needs to free argv[i]
return 0 if ok
*/
int get_windows_argv(int __attribute__((unused)) *pargc, char __attribute__((unused)) ***pargv)
{
#if defined(WIN32) && defined(_UNICODE)
    // copied & modified from mingw-runtime-3.13's init.c
    int _argc = 0;
    wchar_t **_argv = 0;
    wchar_t **dummy_environ = 0;
    _startupinfo start_info;
    start_info.newmode = 0;
    __wgetmainargs(&_argc, &_argv, &dummy_environ, -1, &start_info);

    //printf("\nafter __wgetmainargs; _argc: %d\n", _argc); // DEBUG
    int i;
    for (i = 0; i < _argc; i++) {
        //wprintf(L"_argv[%d] wc: %s\n", i, _argv[i]); // DEBUG
        char utf8_buf[UTF8_FILENAME_SIZE] = "";
        WC_2_UTF8(utf8_buf, _argv[i], UTF8_FILENAME_SIZE);
        //printf("_argv[%d] utf8: %s\n", i, utf8_buf); // DEBUG

        char *dup = strdup(utf8_buf);
        if (NULL == dup) {
            goto error;
        }
        gb_argv[i] = dup;
    }
    *pargc = _argc;
    *pargv = gb_argv;
    return 0;

  error:
    while (--_argc >= 0) {
        free(gb_argv[_argc]);
    }
    return -1;
#endif

    return 0;
}

/*
*/
int get_location_opt(char c, char *optarg)
{
    int ret = 1;
    char *bak = strdup(optarg); // backup for displaying error
    if (NULL == bak) {
        av_log(NULL, AV_LOG_ERROR, "%s: strdup failed\n", gb_argv0);
        return ret;
    }

    const char *delim = ":";
    char *tailptr;

    // info text location
    char *token = strtok(optarg, delim);
    if (NULL == token) {
        goto cleanup;
    }
    gb_L_info_location = strtod(token, &tailptr);
    if ('\0' != *tailptr) { // error
        goto cleanup;
    }

    // time stamp location
    token = strtok (NULL, delim);
    if (NULL == token) {
        ret = 0; // time stamp format is optional
        goto cleanup;
    }
    gb_L_time_location = strtod(token, &tailptr);
    if ('\0' != *tailptr) { // error
        goto cleanup;
    }

    ret = 0;

  cleanup:
    if (0 != ret) {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%c is invalid at '%s'\n", gb_argv0, c, bak);
    }
    free(bak);
    return ret;
}

static const int hex2int[] = {0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,10,11,12,13,14,15};
#define CHAR2INT(p) (hex2int[(p)-'0']) // A-F must be in uppercase
/*
col must be in the correct format RRGGBB (in hex)
*/
rgb_color color_str2rgb_color(color_str col)
{
    return (rgb_color) {CHAR2INT(col[0])*16 + CHAR2INT(col[1]), 
        CHAR2INT(col[2])*16 + CHAR2INT(col[3]), 
        CHAR2INT(col[4])*16 + CHAR2INT(col[5]) };
}

/*
check and convert color_str to rgb_color
return -1 if error
*/
int parse_color(rgb_color *rgb, color_str str)
{
    if (NULL == str || strlen(str) < 6) {
        return -1;
    }
    int i;
    for (i = 0; i < 6; i++) {
        char upper = toupper(str[i]);
        if (upper < '0' || upper > 'F')
            return -1;
        if (upper < 'A' && upper > '9')
            return -1;
        str[i] = upper;
    }
    *rgb = color_str2rgb_color(str);
    //av_log(NULL, AV_LOG_INFO, "parse_color: %s=>%d,%d,%d\n", str, rgb->r, rgb->g, rgb->b); //DEBUG
    return 0;
}

/*
*/
int get_color_opt(char c, rgb_color *color, char *optarg)
{
    if (-1 == parse_color(color, optarg))   {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%c is invalid at '%s' -- must be RRGGBB in hex\n", gb_argv0, c, optarg);
        return 1;
    }
    return 0;
}

/*
*/
int get_format_opt(char c, char *optarg)
{
    int ret = 1;
    char *bak = strdup(optarg); // backup for displaying error
    if (NULL == bak) {
        av_log(NULL, AV_LOG_ERROR, "%s: strdup failed\n", gb_argv0);
        return ret;
    }

    const char *delim = ":";

    // info text font color
    char *token = strtok(optarg, delim);
    if (NULL == token || -1 == parse_color(&gb_F_info_color, token)) {
        goto cleanup;
    }
    // info text font size
    token = strtok (NULL, delim);
    if (NULL == token) {
        goto cleanup;
    }
    char *tailptr;
    gb_F_info_font_size = strtod(token, &tailptr);
    if ('\0' != *tailptr) { // error
        goto cleanup;
    }
    // time stamp font
    token = strtok (NULL, delim);
    if (NULL == token) {
        ret = 0; // time stamp format is optional
        gb_F_ts_fontname = gb_f_fontname;
        gb_F_ts_font_size = gb_F_info_font_size - 1;
        goto cleanup;
    }
    gb_F_ts_fontname = token;
    // time stamp font color
    token = strtok (NULL, delim);
    if (NULL == token || -1 == parse_color(&gb_F_ts_color , token)) {
        goto cleanup;
    }
    // time stamp shadow color
    token = strtok (NULL, delim);
    if (NULL == token || -1 == parse_color(&gb_F_ts_shadow  , token)) {
        goto cleanup;
    }
    // time stamp font size
    token = strtok (NULL, delim);
    if (NULL == token) {
        goto cleanup;
    }
    gb_F_ts_font_size = strtod(token, &tailptr);
    if ('\0' != *tailptr) { // error
        goto cleanup;
    }

    ret = 0;

  cleanup:
    //av_log(NULL, AV_LOG_INFO, "%s:%.1f:", format_color(gb_F_info_color), gb_F_info_font_size); // DEBUG
    //av_log(NULL, AV_LOG_INFO, "%s:%s:", gb_F_ts_fontname, format_color(gb_F_ts_color)); // DEBUG
    //av_log(NULL, AV_LOG_INFO, "%s:%.1f\n", format_color(gb_F_ts_shadow), gb_F_ts_font_size); // DEBUG
    if (0 != ret) {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%c is invalid at '%s'\n", gb_argv0, c, bak);
        av_log(NULL, AV_LOG_ERROR, "examples:\n");
        av_log(NULL, AV_LOG_ERROR, "info text blue color size 10:\n  -%c 0000FF:10\n", c);
        av_log(NULL, AV_LOG_ERROR, "info text green color size 12; time stamp font comicbd.ttf yellow color black shadow size 8 :\n  -%c 00FF00:12:comicbd.ttf:ffff00:000000:8\n", c);
    }
    free(bak);
    return ret;
}

/*
*/
int get_int_opt(char *c, int *opt, char *optarg, int sign)
{
    char *tailptr;
    int ret = strtol(optarg, &tailptr, 10);
    if ('\0' != *tailptr) { // error
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%s is invalid at '%s'\n", gb_argv0, c, tailptr);
        return 1;
    }
    if (sign > 0 && ret <= 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%s must be > 0\n", gb_argv0, c);
        return 1;
    } else if (sign == 0 && ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%s must be >= 0\n", gb_argv0, c);
        return 1;
    }
    *opt = ret;
    return 0;
}

int get_double_opt(char c, double *opt, char *optarg, double sign)
{
    char *tailptr;
    double ret = strtod(optarg, &tailptr);
    if ('\0' != *tailptr) { // error
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%c is invalid at '%s'\n", gb_argv0, c, tailptr);
        return 1;
    }
    if (sign > 0 && ret <= 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%c must be > 0\n", gb_argv0, c);
        return 1;
    } else if (sign == 0.0 && ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: argument for option -%c must be >= 0\n", gb_argv0, c);
        return 1;
    }
    *opt = ret;
    return 0;
}

char* mtn_identification()
{
    const char txt[] = "Movie Thumbnailer (mtn) %s\nCompiled%s with: %s %s %s %s GD:%s";
	const char GD_VER[] = 
	   #ifdef GD_VERSION_STRING
           GD_VERSION_STRING
       #else
           GD2_ID
        #endif
	;
    const char STATIC_MSG[] =
        #ifdef MTN_STATIC
            " statically"
        #else
            ""
        #endif
            ;
    size_t s = snprintf(NULL, 0, txt, gb_version, STATIC_MSG, LIBAVCODEC_IDENT, LIBAVFORMAT_IDENT, LIBAVUTIL_IDENT, LIBSWSCALE_IDENT, GD_VER) +1;
	char* msg = malloc(s);
               snprintf( msg, s, txt, gb_version, STATIC_MSG, LIBAVCODEC_IDENT, LIBAVFORMAT_IDENT, LIBAVUTIL_IDENT, LIBSWSCALE_IDENT, GD_VER);
	return msg;
}

void
usage()
{
    av_log(NULL, AV_LOG_INFO, "\n%s\n\n", mtn_identification());

    av_log(NULL, AV_LOG_INFO, "Mtn saves thumbnails of specified movie files or directories to image files.\n");
    av_log(NULL, AV_LOG_INFO, "For directories, it will recursively search inside for movie files.\n\n");
    av_log(NULL, AV_LOG_INFO, "Usage:\n  %s [options] file_or_dir1 [file_or_dir2] ... [file_or_dirn]\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "Options: (and default values)\n");
    av_log(NULL, AV_LOG_INFO, "  -a aspect_ratio : override input file's display aspect ratio\n");
    av_log(NULL, AV_LOG_INFO, "  -b %.2f : skip if %% blank is higher; 0:skip all 1:skip really blank >1:off\n", GB_B_BLANK);
    av_log(NULL, AV_LOG_INFO, "  -B %.1f : omit this seconds from the beginning\n", GB_B_BEGIN);
    av_log(NULL, AV_LOG_INFO, "  -c %d : # of column\n", GB_C_COLUMN);
    av_log(NULL, AV_LOG_INFO, "  -C %d : cut movie and thumbnails not more than the specified seconds; <=0:off\n", GB_C_CUT);
    av_log(NULL, AV_LOG_INFO, "  -d #: recursion depth; 0:immediate children files only\n");
    av_log(NULL, AV_LOG_INFO, "  -D %d : edge detection; 0:off >0:on; higher detects more; try -D4 -D6 or -D8\n", gb_D_edge);
    //av_log(NULL, AV_LOG_ERROR, "  -e : to be done\n"); // extension of movie files
    av_log(NULL, AV_LOG_INFO, "  -E %.1f : omit this seconds at the end\n", GB_E_END);
    av_log(NULL, AV_LOG_INFO, "  -f %s : font file; use absolute path if not in usual places\n", GB_F_FONTNAME);
    av_log(NULL, AV_LOG_INFO, "  -F RRGGBB:size[:font:RRGGBB:RRGGBB:size] : font format [time is optional]\n     info_color:info_size[:time_font:time_color:time_shadow:time_size]\n");
    av_log(NULL, AV_LOG_INFO, "  -g %d : gap between each shot\n", GB_G_GAP);
    av_log(NULL, AV_LOG_INFO, "  -h %d : minimum height of each shot; will reduce # of column to fit\n", GB_H_HEIGHT);
    av_log(NULL, AV_LOG_INFO, "  -H : filesize only in human readable format (MiB, GiB). Default shows size in bytes too\n");
    av_log(NULL, AV_LOG_INFO, "  -i : info text off\n");
    av_log(NULL, AV_LOG_INFO, "  -I : save individual shots too\n");
    av_log(NULL, AV_LOG_INFO, "  -j %d : jpeg quality\n", GB_J_QUALITY);
    av_log(NULL, AV_LOG_INFO, "  -k RRGGBB : background color (in hex)\n"); // backgroud color
    av_log(NULL, AV_LOG_INFO, "  -L info_location[:time_location] : location of text\n     1=lower left, 2=lower right, 3=upper right, 4=upper left\n");
    av_log(NULL, AV_LOG_INFO, "  -n : run at normal priority\n");
    av_log(NULL, AV_LOG_INFO, "  -N info_suffix : save info text to a file with suffix\n");
    av_log(NULL, AV_LOG_INFO, "  -o %s : output suffix including image extension (.jpg or .png)\n", GB_O_SUFFIX);
    av_log(NULL, AV_LOG_INFO, "  -O directory : save output files in the specified directory\n");
    av_log(NULL, AV_LOG_INFO, "  -p : pause before exiting; default on in win32\n");
    av_log(NULL, AV_LOG_INFO, "  -P : don't pause before exiting; override -p\n");
    av_log(NULL, AV_LOG_INFO, "  -q : quiet mode (print only error messages)\n");
    av_log(NULL, AV_LOG_INFO, "  -r %d : # of rows; >0:override -s\n", GB_R_ROW);
    av_log(NULL, AV_LOG_INFO, "  -s %d : time step between each shot\n", GB_S_STEP);
    av_log(NULL, AV_LOG_INFO, "  -S #: select specific stream number\n");
    av_log(NULL, AV_LOG_INFO, "  -t : time stamp off\n");
    av_log(NULL, AV_LOG_INFO, "  -T text : add text above output image\n");
    av_log(NULL, AV_LOG_INFO, "  -v : verbose mode (debug)\n");
    av_log(NULL, AV_LOG_INFO, "  -w %d : width of output image; 0:column * movie width\n", GB_W_WIDTH);
    av_log(NULL, AV_LOG_INFO, "  -W : don't overwrite existing files, i.e. update mode\n");
    av_log(NULL, AV_LOG_INFO, "  -X : use full input filename (include extension)\n");
    av_log(NULL, AV_LOG_INFO, "  -z : always use seek mode\n");
    av_log(NULL, AV_LOG_INFO, "  -Z : always use non-seek mode -- slower but more accurate timing\n");
    av_log(NULL, AV_LOG_INFO, "  --shadow[=N]\n     draw shadows beneath thumbnails with radius N pixels if N >0; Radius is calculated if N=0 or N is omitted\n");
    av_log(NULL, AV_LOG_INFO, "  --transparent\n    set background color (-k) to transparent; works with PNG image only \n");
    av_log(NULL, AV_LOG_INFO, "  --cover[=_cover.jpg]\n    extract album art if exists \n");
    av_log(NULL, AV_LOG_INFO, "  file_or_dirX\n       name of the movie file or directory containing movie files\n\n");
    av_log(NULL, AV_LOG_INFO, "Examples:\n");
    av_log(NULL, AV_LOG_INFO, "  to save thumbnails to file infile%s with default options:\n    %s infile.avi\n", GB_O_SUFFIX, gb_argv0);
    av_log(NULL, AV_LOG_INFO, "  to change time step to 65 seconds & change total width to 900:\n    %s -s 65 -w 900 infile.avi\n", gb_argv0);
    // as of version 0.60, -s 0 is not needed
    av_log(NULL, AV_LOG_INFO, "  to step evenly to get 3 columns x 10 rows:\n    %s -c 3 -r 10 infile.avi\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "  to save output files to writeable directory:\n    %s -O writeable /read/only/dir/infile.avi\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "  to get 2 columns in original movie size:\n    %s -c 2 -w 0 infile.avi\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "  to skip uninteresting shots, try:\n    %s -D 6 infile.avi\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "  to draw shadows of the individual shots, try:\n    %s --shadow=3 -g 7 infile.avi\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "  to skip warning messages to be printed to console (useful for flv files producing lot of warnings), try:\n    %s -q infile.avi\n", gb_argv0);
#ifdef WIN32
    av_log(NULL, AV_LOG_INFO, "\nIn windows, you can run %s from command prompt or drag files/dirs from\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "windows explorer and drop them on %s. you can change the default options\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "by creating a shortcut to %s and add options there (right click the\n", gb_argv0);
    av_log(NULL, AV_LOG_INFO, "shortcut -> Properties -> Target); then drop files/dirs on the shortcut\n");
    av_log(NULL, AV_LOG_INFO, "instead.\n");
#else
    av_log(NULL, AV_LOG_INFO, "\nYou'll probably need to change the truetype font path (-f fontfile).\n");
    av_log(NULL, AV_LOG_INFO, "the default is set to %s which might not exist in non-windows\n", GB_F_FONTNAME);
    av_log(NULL, AV_LOG_INFO, "systems. if you don't have a truetype font, you can turn the text off by\n");
    av_log(NULL, AV_LOG_INFO, "using -i -t.\n");
#endif
    av_log(NULL, AV_LOG_INFO, "\nMtn comes with ABSOLUTELY NO WARRANTY. this is free software, and you are\n");
    av_log(NULL, AV_LOG_INFO, "welcome to redistribute it under certain conditions; for details see file\n");
    av_log(NULL, AV_LOG_INFO, "gpl-2.0.txt.\n\n");

    av_log(NULL, AV_LOG_INFO, "wahibre@gmx.com\n");
    av_log(NULL, AV_LOG_INFO, "https://gitlab.com/movie_thumbnailer/mtn/wikis\n");
}

/**
 * @return 0- success, otherwise - failed
 */
int main(int argc, char *argv[])
{
    int return_code = -1;

    gb_argv0 = path_2_file(argv[0]);
    setvbuf(stderr, NULL, _IONBF, 0); // turn off buffering in mingw

    gb_st_start = time(NULL); // program start time
    srand(gb_st_start);

    // get utf-8 argv in windows
    if (0 != get_windows_argv(&argc, &argv)) {
        av_log(NULL, AV_LOG_ERROR, "%s: cannot get command line arguments\n", gb_argv0);
        return -1;
    }

    // set locale
    __attribute__((unused)) char *locale = setlocale(LC_ALL, "");
    //av_log(NULL, AV_LOG_VERBOSE, "locale: %s\n", locale);

    /* get & check options */
    
	struct option long_options[] = {		// no_argument, required_argument, optional_argument
		{"shadow",      optional_argument, 	0,  0 },
		{"transparent", no_argument, 		0,  0 },
		{"cover",       optional_argument, 	0,  0 },
		{0,         	0,                 	0,  0 }
	};    
    int parse_error = 0, option_index = 0;
    int c;
    while (-1 != (c = getopt_long(argc, argv, "a:b:B:c:C:d:D:E:f:F:g:h:HiIj:k:L:nN:o:O:pPqr:s:S:tT:vVw:WXzZ", long_options, &option_index))) {
        double tmp_a_ratio = 0;
        switch (c) {
        case 0:
			if(strcmp("shadow", long_options[option_index].name) == 0)
			{
				if(optarg)
					parse_error += get_int_opt("-shadow", &gb__shadow, optarg, 0);
				else
					gb__shadow = 0;				
			}
			else
			{
				if(strcmp("transparent", long_options[option_index].name) == 0)
					gb__transparent_bg = 1;
                else
                {
                    if(strcmp("cover", long_options[option_index].name) == 0)
                    {
                        gb__cover = 1;

                        if(optarg)
                            gb__cover_suffix = optarg;
                    }
                }
			}
			break;
        case 'a':
            if (0 == get_double_opt('a', &tmp_a_ratio, optarg, 1)) { // success
                gb_a_ratio.num = tmp_a_ratio * 10000;
                gb_a_ratio.den = 10000;
            } else {
                parse_error++;
            }
            break;
//		case 'A':
        case 'b':
            parse_error += get_double_opt('b', &gb_b_blank, optarg, 0);
            if (gb_b_blank < .2) {
                av_log(NULL, AV_LOG_INFO, "%s: -b %.2f might be too extreme; try -b .5\n", gb_argv0, gb_b_blank);
            }
            if (gb_b_blank > 1) {
                // turn edge detection off cuz it requires blank detection
                gb_D_edge = 0;
            }
            break;
        case 'B':
            parse_error += get_double_opt('B', &gb_B_begin, optarg, 0);
            break;
        case 'c':
            parse_error += get_int_opt("c", &gb_c_column, optarg, 1);
            break;
        case 'C':
            parse_error += get_double_opt('C', &gb_C_cut, optarg, 1);
            break;
        case 'd':
            parse_error += get_int_opt("d", &gb_d_depth, optarg, 0);
            break;
        case 'D':
            parse_error += get_int_opt("D", &gb_D_edge, optarg, 0);
            if (gb_D_edge > 0 
                && (gb_D_edge < 4 || gb_D_edge > 12)) {
                av_log(NULL, AV_LOG_INFO, "%s: -D%d might be too extreme; try -D4, -D6, or -D8\n", gb_argv0, gb_D_edge);
            }
            break;
//		case 'e':
            //gb_e_ext = optarg;
            //break;
        case 'E':
            parse_error += get_double_opt('E', &gb_E_end, optarg, 0);
            break;
        case 'f':
            gb_f_fontname = optarg;
            if (0 == strcmp(gb_F_ts_fontname, GB_F_FONTNAME)) {
                gb_F_ts_fontname = gb_f_fontname;
            }
            break;
        case 'F':
            parse_error += get_format_opt('F', optarg);
            break;
        case 'g':
            parse_error += get_int_opt("g", &gb_g_gap, optarg, 0);
            break;
//		case 'G':
        case 'h':
            parse_error += get_int_opt("h", &gb_h_height, optarg, 0);
            break;
        case 'H':
            gb_H_human_filesize = 1;
            break;
        case 'i':
            gb_i_info = 0;
            break;
        case 'I':
            gb_I_individual = 1;
            break;
        case 'j':
            parse_error += get_int_opt("j", &gb_j_quality, optarg, 1);
            break;
//		case 'J':
        case 'k': // background color
            parse_error += get_color_opt('k', &gb_k_bcolor, optarg);
            break;
//		case 'K':
//      case 'l':
        case 'L':
            parse_error += get_location_opt('L', optarg);
            break;
//		case 'm':
//		case 'M':
        case 'n':
            gb_n_normal = 1; // normal priority
            break;
        case 'N':
            gb_N_suffix = optarg;
            break;
        case 'o':
            gb_o_suffix = optarg;
            break;
        case 'O':
            gb_O_outdir = optarg;
            rem_trailing_slash(gb_O_outdir);
            break;
        case 'p':
            gb_p_pause = 1; // pause before exiting
            break;
        case 'P':
            gb_P_dontpause = 1; // dont pause
            break;
        case 'q':
            gb_q_quiet = 1; //quiet
            break;
//		case 'Q':
        case 'r':
            parse_error += get_int_opt("r", &gb_r_row, optarg, 0);
            break;
//		case 'R':
        case 's':
            parse_error += get_int_opt("s", &gb_s_step, optarg, 0);
            break;
        case 'S':
            parse_error += get_int_opt("S", &gb_S_select_video_stream, optarg, 0);
            break;
        case 't':
            gb_t_timestamp = 0; // off
            break;
        case 'T':
            gb_T_text = optarg;
            break;
//		case 'u':
//		case 'U':
        case 'v':
            gb_v_verbose = 1; // verbose
            break;
        case 'V':
            gb_V = 1; // DEBUG
            av_log(NULL, AV_LOG_INFO, "%s: -V is only used for debugging\n", gb_argv0);
            break;
        case 'w':
            parse_error += get_int_opt("w", &gb_w_width, optarg, 0);
            break;
        case 'W':
            gb_W_overwrite = 0;
            break;
//		case 'x':
        case 'X':
            gb_X_filename_use_full = 1;
            break;
//		case 'y':
//		case 'Y':
        case 'z':
            gb_z_seek = 1; // always seek mode
            break;
        case 'Z':
            gb_Z_nonseek = 1; // always non-seek mode
            break;
        default:
            parse_error += 1;
            break;
        }
    }

    if (optind == argc) {
        //av_log(NULL, AV_LOG_ERROR, "%s: no input files or directories specified", gb_argv0);
        parse_error += 1;
    }
    
    /* check arguments */
    if (gb_r_row == 0 && gb_s_step == 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: option -r and -s cant be 0 at the same time", gb_argv0);
        parse_error += 1;
    }
    if (gb_b_blank > 1 && gb_D_edge > 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: -D requires -b arg to be less than 1", gb_argv0);
        parse_error += 1;
    }
    if (gb_z_seek == 1 && gb_Z_nonseek == 1) {
        av_log(NULL, AV_LOG_ERROR, "%s: option -z and -Z cant be used together", gb_argv0);
        parse_error += 1;
    }
    if (gb_E_end > 0 && gb_C_cut > 0) {
        av_log(NULL, AV_LOG_ERROR, "%s: option -C and -E cant be used together", gb_argv0);
        parse_error += 1;
    }

    if (0 != parse_error) {
        usage();
        goto exit;
    }

    /* lower priority */
    if (1 != gb_n_normal) { // lower priority
#ifdef WIN32
        SetPriorityClass(GetCurrentProcess(), IDLE_PRIORITY_CLASS);
#else
		errno = 0;
        int nice_ret = nice(10); // mingw doesn't have nice??
        //setpriority (PRIO_PROCESS, 0, PRIO_MAX/2);
		if(nice_ret == -1 && errno != 0)
			av_log(NULL, AV_LOG_ERROR, "error setting process priority (nice=10)\n");
#endif
    }

    /* create output directory */
    if (NULL != gb_O_outdir && !is_dir(gb_O_outdir)) {
#ifdef WIN32
        int ret = mkdir(gb_O_outdir);
#else
        int ret = mkdir(gb_O_outdir, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
#endif
        if (0 != ret) {
            av_log(NULL, AV_LOG_ERROR, "\n%s: creating output directory '%s' failed: %s\n", gb_argv0, gb_O_outdir, strerror(errno));
            goto exit;
        }
    }

    /* init */
#if LIBAVFORMAT_VERSION_INT < AV_VERSION_INT(58, 9, 100)
    av_register_all();          // Register all formats and codecs
#endif
	if(gb_q_quiet>0)
		av_log_set_level(AV_LOG_ERROR);
	else
	{		
		if (gb_v_verbose > 0)
			av_log_set_level(AV_LOG_VERBOSE);
		else
			av_log_set_level(AV_LOG_INFO);
	}
		
	// display mtn+libraries versions for bug reporting
	av_log(NULL, AV_LOG_VERBOSE, "%s\n\n", mtn_identification());
		
    //gdUseFontConfig(1); // set GD to use fontconfig patterns

    /* process movie files */
    return_code = process_loop(argc - optind, argv + optind, 0);

  exit:
    // clean up
#if defined(WIN32) && defined(_UNICODE)
    while (--argc >= 0) {
        free(argv[argc]);
    }
#endif

    //av_log(NULL, AV_LOG_VERBOSE, "\n%s: total run time: %.2f s.\n", gb_argv0, difftime(time(NULL), gb_st_start));

    if (1 == gb_p_pause && 0 == gb_P_dontpause) {
        av_log(NULL, AV_LOG_ERROR, "\npausing... press Enter key to exit (see -P option)\n");
        fflush(stdout);
        fflush(stderr);
        getchar();
    }
    return return_code;
}
