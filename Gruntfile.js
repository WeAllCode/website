module.exports = function(grunt) {
    'use strict';

    // load custom tasks
    require('time-grunt')(grunt);
    require('load-grunt-tasks')(grunt);

    // initialize the configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        files: {
            grunt: 'Gruntfile.js',
            root: 'coderdojochi',
            static: '<%= files.root %>/static',
            templates: '<%= files.root %>/templates',
            css: '<%= files.static %>/css',
            sass: '<%= files.static %>/scss',
            js: '<%= files.static %>/js',
            img: '<%= files.static %>/images',
            sprites: '<%= files.static %>/sprites',
            sourceMap: 'cdc.min.map'
        },

        autoprefixer: {

            options: {
                map: true,
                browsers: ['Firefox > 25', 'last 4 versions', '> 3%', 'ie 8']
            },

            dev: { 
                expand: true,
                flatten: true,
                src: [
                    '<%= files.css %>/*.css', 
                    '!<%= files.css %>/*.min.css'
                ],
                dest: '<%= files.css %>/' 
            }
        },

        compass: {
            dist: {
                options: {
                    require: ['susy', 'breakpoint'],
                    sassDir: '<%= files.sass %>',
                    cssDir: '<%= files.css %>',
                    imagesDir: '<%= files.img %>',
                    raw: 'sprite_load_path = "<%= files.sprites %>"\n',
                    httpGeneratedImagesPath: '../images',
                    environment: 'production',
                    outputStyle: 'compressed',
                    debugInfo: false,
                    noLineComments: true,
                    force: true
                }
            },
            dev: {
                options: {
                    require: ['susy', 'breakpoint'],
                    sassDir: '<%= files.sass %>',
                    cssDir: '<%= files.css %>',
                    imagesDir: '<%= files.img %>',
                    raw: 'sprite_load_path = "<%= files.sprites %>"\n',
                    httpGeneratedImagesPath: '../images',
                    outputStyle: 'expanded',
                    debugInfo: true
                }
            }
        },

        concurrent: {
            dev : [
                'watch', 
                'shell:django'
            ],
            options: {
                logConcurrentOutput: true
            }
        },

        cssmin: {
            minify: {
                src: [
                    '<%= files.css %>/cdc.css'
                ],
                dest: '<%= files.css %>/cdc.min.css'
            }
        },

        imageoptim: {
            src: [
                '<%= files.img %>'
            ],
            options: {
                jpegMini: true,
                imageAlpha: true,
                quitAfter: true
            }
        },

        jsbeautifier: {
            files: [
                '<%= files.js %>/**/*.js',
                '!<%= files.js %>/**/*.min.js',
                '!<%= files.js %>/vendor/**/*.js'
            ]
        },

        jshint: {
            files: [
                '<%= files.js %>/**/*.js'
            ],
            options: {
                forin: true,
                noarg: true,
                noempty: true,
                eqeqeq: true,
                bitwise: true,
                strict: true,
                undef: true,
                curly: true,
                expr: true,
                browser: true,
                jquery: true,
                es3: true,
                ignores: [
                    '<%= files.js %>/*.min.js',
                    '<%= files.js %>/vendor/**/*.js'
                ],
                // ignore certain warnings
                '-W097': true, // strict must be contained in function (browserify will wrap them on compile)
                '-W117': true, // globals are not defined
                '-W069': true, // arrays should be in dot notation
                '-W016': true, // Unexpected use of '>>>'.
                '-W061': true  // eval can be harmful
            }
        },

        shell: {
            django: {
                command: 'python manage.py runserver 0.0.0.0:8000',
                options: {
                    stdout: true,
                    stdin: true,
                    stderr: true
                }
            }
        },

        uncss: {
            dist: {
                files: {
                    '<%= files.css %>/cdc.min.css': [
                        '<%= files.templates %>/**/*.html'
                    ]
                }
            }
        },

        uglify: {
            dist: {
                options: {
                    sourceMap: true,
                    sourceMapName: '<%= files.js %>/cdc.min.map'
                },
                files: {
                    '<%= files.js %>/cdc.min.js': [
                        '<%= files.js %>/vendor/*.js',
                        '<%= files.js %>/*.js',
                        '!<%= files.js %>/*.min.js'
                    ]
                }
            }
        },

        watch: {
            
            scripts: {
                files: [
                    '<%= files.grunt %>',
                    '<%= files.js %>/**/*.js',
                    '!<%= files.js %>/*.min.js',
                    '!<%= files.js %>/vendor/*.js',
                ],
                tasks: [
                    'jsbeautifier',
                    'jshint'
                ],
                options: {
                    livereload: true
                }
            },
            
            scss: {
                files: ['<%= files.sass %>/**/*.scss'],
                tasks: [
                    'compass:dev',
                    'autoprefixer:dev'
                ]
            },

            css: {
                files: ['<%= files.css %>/**/*.css'],
                options: {
                    livereload: true
                }
            }
        }
    });

    
    // register tasks
    
    grunt.registerTask('default', [ // $ grunt
        'jsbeautifier',
        'jshint',
        'concurrent:dev'
    ]);

    grunt.registerTask('build', [ // $ grunt build
        'jsbeautifier',
        'jshint',
        'uglify:dist',
        'compass:dist',
        'autoprefixer:dev',
        'cssmin'
        //'uncss:dist'
    ]);
};
